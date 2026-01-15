"""Question supervision node for multi-question flows."""

from pathlib import Path

from ai_prompter import Prompter
from langchain_core.output_parsers import PydanticOutputParser

from quiz_me.models import SupervisionResult
from quiz_me.states import MultiQuestionState

# Prompts directory for ai-prompter
PROMPTS_DIR = str(Path(__file__).parent.parent / "prompts")


async def supervise_multi_node(state: MultiQuestionState) -> dict:
    """Review a generated question in multi-question flow.

    This node:
    1. Renders the supervision prompt with the current question
    2. Invokes the supervisor model
    3. Parses the response into a SupervisionResult
    4. Updates state with approval status and feedback

    Args:
        state: Current flow state containing the question to review

    Returns:
        Dict with updated state fields
    """
    config = state.config
    question = state.current_question

    if question is None:
        return {
            "current_supervision_result": SupervisionResult(
                approved=False,
                feedback="No question to supervise - generation failed",
                severity="critical",
            ),
        }

    parser = PydanticOutputParser(pydantic_object=SupervisionResult)

    # Build prompt context
    prompt_context = {
        "content": config.content,
        "topic": config.topic,
        "language": config.language,
        "question": {
            "question_type": question.question_type.value,
            "statement": question.statement,
            "alternatives": question.alternatives,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "difficulty": question.difficulty,
        },
        "supervisor_instructions": config.supervisor_instructions,
        "format_instructions": parser.get_format_instructions(),
    }

    # Render the prompt
    prompter = Prompter(prompt_template="supervise_question", prompt_dir=PROMPTS_DIR)
    prompt = prompter.render(prompt_context)

    try:
        # Invoke the supervisor model
        response = await config.supervisor_model.ainvoke(prompt)

        # Extract content from response
        content = response.content if hasattr(response, "content") else str(response)

        # Parse the response
        result = parser.parse(content)

        # Prepare state updates
        updates = {
            "current_supervision_result": result,
        }

        # If rejected, store feedback for retry
        if not result.approved:
            updates["current_supervisor_feedback"] = result.feedback
            updates["current_retry_count"] = state.current_retry_count + 1
            updates["total_retries"] = state.total_retries + 1

        return updates

    except Exception as e:
        # If supervision fails, treat as rejection
        return {
            "current_supervision_result": SupervisionResult(
                approved=False,
                feedback=f"Supervision error: {str(e)}",
                severity="critical",
            ),
            "current_supervisor_feedback": f"Supervision error: {str(e)}",
        }
