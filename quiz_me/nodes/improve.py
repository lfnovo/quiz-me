"""Question improvement node for regenerating questions based on feedback."""

from pathlib import Path

from ai_prompter import Prompter
from langchain_core.output_parsers import PydanticOutputParser

from quiz_me.models import Question

# Prompts directory for ai-prompter
PROMPTS_DIR = str(Path(__file__).parent.parent / "prompts")


async def improve_question_node(
    original_question: Question,
    feedback: str,
    content: str | None,
    topic: str | None,
    question_type: str,
    language: str | None,
    generator_instructions: str | None,
    generator_model,
) -> Question:
    """Generate an improved version of a question based on feedback.

    This function:
    1. Takes the original question and feedback
    2. Renders the generation prompt with improvement context
    3. Invokes the generator model
    4. Returns the improved question

    Args:
        original_question: The question to improve
        feedback: User/supervisor feedback describing what to fix
        content: Original content (if available)
        topic: Original topic (if available)
        question_type: The question type to maintain
        language: Target language for generation
        generator_instructions: Domain-specific instructions
        generator_model: LangChain-compatible model

    Returns:
        Improved Question object

    Raises:
        Exception: If generation or parsing fails
    """
    parser = PydanticOutputParser(pydantic_object=Question)

    # Build prompt context with original question for improvement
    prompt_context = {
        "question_type": question_type,
        "content": content,
        "topic": topic,
        "language": language,
        "generator_instructions": generator_instructions,
        "format_instructions": parser.get_format_instructions(),
        "supervisor_feedback": feedback,
        "original_question": {
            "statement": original_question.statement,
            "alternatives": original_question.alternatives,
            "correct_answer": original_question.correct_answer,
            "explanation": original_question.explanation,
        },
    }

    # Render the prompt
    prompter = Prompter(prompt_template="generate_question", prompt_dir=PROMPTS_DIR)
    prompt = prompter.render(prompt_context)

    # Invoke the model
    response = await generator_model.ainvoke(prompt)

    # Extract content from response
    content_str = response.content if hasattr(response, "content") else str(response)

    # Parse the response
    improved_question = parser.parse(content_str)

    return improved_question
