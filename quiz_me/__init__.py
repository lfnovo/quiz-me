"""Quiz-Me: AI-powered question generation library using Langgraph flows."""

import time

from quiz_me.config import (
    BaseGeneratorConfig,
    MultiQuestionConfig,
    QuestionTypeMix,
    SingleQuestionConfig,
)
from quiz_me.flows.multi import multi_question_flow
from quiz_me.flows.single import single_question_flow
from quiz_me.models import (
    GenerationError,
    GenerationResult,
    MultiGenerationResult,
    Question,
    QuestionPlan,
    QuestionSpec,
    QuestionType,
    SupervisionResult,
)
from quiz_me.states import (
    MultiQuestionState,
    SingleQuestionState,
)


async def generate_question(config: SingleQuestionConfig) -> GenerationResult:
    """Generate a single question from content or topic.

    This is the main public API for single question generation.
    It wraps the Langgraph flow and returns a clean result.

    Args:
        config: Configuration for generation including content/topic,
                question type, model, and optional supervision settings.

    Returns:
        GenerationResult containing the generated question and metadata.

    Raises:
        GenerationError: If generation fails after all retries.

    Example:
        ```python
        from langchain_openai import ChatOpenAI
        from quiz_me import generate_question, SingleQuestionConfig, QuestionType

        config = SingleQuestionConfig(
            content="Python is a programming language...",
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=ChatOpenAI(model="gpt-4"),
        )

        result = await generate_question(config)
        print(result.question.statement)
        ```
    """
    # Create initial state
    initial_state = SingleQuestionState(config=config)

    # Track timing
    start_time = time.perf_counter()

    # Run the flow with increased recursion limit for complex supervision loops
    final_state = await single_question_flow.ainvoke(initial_state, {"recursion_limit": 50})

    # Calculate elapsed time
    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    # Extract the question from final state
    # Handle both dict and Pydantic model returns from Langgraph
    if isinstance(final_state, dict):
        question = final_state.get("current_question")
        error = final_state.get("error")
        retry_count = final_state.get("retry_count", 0)
        supervision_result = final_state.get("supervision_result")
    else:
        question = final_state.current_question
        error = final_state.error
        retry_count = final_state.retry_count
        supervision_result = final_state.supervision_result

    # Check for errors
    if question is None:
        raise GenerationError(
            message=error or "Failed to generate question",
            last_attempt=None,
            retry_count=retry_count,
        )

    # Update question with supervision status if applicable
    if supervision_result is not None:
        # Create a new question with updated approval status
        question = Question(
            statement=question.statement,
            question_type=question.question_type,
            alternatives=question.alternatives,
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            difficulty=question.difficulty,
            approved=supervision_result.approved,
            supervision_feedback=supervision_result.feedback if not supervision_result.approved else None,
        )

    return GenerationResult(
        question=question,
        retries_used=retry_count,
        generation_time_ms=elapsed_ms,
    )


async def generate_questions(config: MultiQuestionConfig) -> MultiGenerationResult:
    """Generate multiple questions from content or topic.

    This is the main public API for multi-question generation.
    It wraps the Langgraph flow and returns a clean result.

    The flow:
    1. Plans the questions (determines focus areas and types)
    2. Generates each question according to the plan
    3. Optionally supervises each question
    4. Returns all generated questions

    Args:
        config: Configuration for generation including content/topic,
                num_questions, optional question_mix, model, and
                optional supervision settings.

    Returns:
        MultiGenerationResult containing all generated questions,
        the plan that was executed, and metadata.

    Raises:
        GenerationError: If generation fails completely.

    Example:
        ```python
        from langchain_openai import ChatOpenAI
        from quiz_me import generate_questions, MultiQuestionConfig, QuestionTypeMix, QuestionType

        config = MultiQuestionConfig(
            content="Python is a programming language...",
            num_questions=5,
            question_mix=[
                QuestionTypeMix(question_type=QuestionType.MULTIPLE_CHOICE, count=3),
                QuestionTypeMix(question_type=QuestionType.OPEN_ENDED, count=2),
            ],
            generator_model=ChatOpenAI(model="gpt-4"),
        )

        result = await generate_questions(config)
        for q in result.questions:
            print(q.statement)
        ```
    """
    # Create initial state
    initial_state = MultiQuestionState(config=config)

    # Track timing
    start_time = time.perf_counter()

    # Run the flow with increased recursion limit for complex supervision loops
    final_state = await multi_question_flow.ainvoke(initial_state, {"recursion_limit": 50})

    # Calculate elapsed time
    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    # Extract results from final state
    # Handle both dict and Pydantic model returns from Langgraph
    if isinstance(final_state, dict):
        questions = final_state.get("questions", [])
        plan = final_state.get("plan")
        total_retries = final_state.get("total_retries", 0)
        error = final_state.get("error")
    else:
        questions = final_state.questions
        plan = final_state.plan
        total_retries = final_state.total_retries
        error = final_state.error

    # Check for errors
    if plan is None:
        raise GenerationError(
            message=error or "Failed to create question plan",
            last_attempt=None,
            retry_count=0,
        )

    if not questions:
        raise GenerationError(
            message=error or "Failed to generate any questions",
            last_attempt=None,
            retry_count=total_retries,
        )

    return MultiGenerationResult(
        questions=questions,
        plan=plan,
        total_retries_used=total_retries,
        generation_time_ms=elapsed_ms,
    )


async def improve_question(
    question: Question,
    feedback: str,
    config: SingleQuestionConfig,
) -> GenerationResult:
    """Improve an existing question based on feedback.

    This function regenerates a question incorporating the provided feedback,
    using the same pattern as the supervision retry flow.

    Args:
        question: The original question to improve.
        feedback: Specific feedback describing what to fix or improve.
        config: Configuration including the generator model and settings.
                The question_type should match the original question.

    Returns:
        GenerationResult containing the improved question.

    Raises:
        GenerationError: If improvement fails.

    Example:
        ```python
        from quiz_me import improve_question, SingleQuestionConfig, QuestionType

        # Original question that needs improvement
        original = result.question

        # Improve based on feedback
        config = SingleQuestionConfig(
            content="Original content...",
            question_type=original.question_type,
            generator_model=model,
        )

        improved = await improve_question(
            question=original,
            feedback="The distractors are too obvious. Make them more plausible.",
            config=config,
        )
        print(improved.question.statement)
        ```
    """
    from quiz_me.nodes.improve import improve_question_node

    # Track timing
    start_time = time.perf_counter()

    try:
        # Generate improved question
        improved = await improve_question_node(
            original_question=question,
            feedback=feedback,
            content=config.content,
            topic=config.topic,
            question_type=config.question_type.value,
            language=config.language,
            generator_instructions=config.generator_instructions,
            generator_model=config.generator_model,
        )

        # Calculate elapsed time
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return GenerationResult(
            question=improved,
            retries_used=0,
            generation_time_ms=elapsed_ms,
        )

    except Exception as e:
        raise GenerationError(
            message=f"Failed to improve question: {str(e)}",
            last_attempt=question,
            retry_count=0,
            original_error=e,
        )


__all__ = [
    # Config
    "BaseGeneratorConfig",
    "SingleQuestionConfig",
    "MultiQuestionConfig",
    "QuestionTypeMix",
    # Models
    "Question",
    "QuestionType",
    "QuestionSpec",
    "QuestionPlan",
    "SupervisionResult",
    "GenerationResult",
    "MultiGenerationResult",
    "GenerationError",
    # States
    "SingleQuestionState",
    "MultiQuestionState",
    # Functions
    "generate_question",
    "generate_questions",
    "improve_question",
]
