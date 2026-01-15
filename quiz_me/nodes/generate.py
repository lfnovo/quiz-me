"""Question generation node for Langgraph flows."""

from pathlib import Path

from ai_prompter import Prompter
from langchain_core.output_parsers import PydanticOutputParser

from quiz_me.models import Question
from quiz_me.states import SingleQuestionState

# Prompts directory for ai-prompter
PROMPTS_DIR = str(Path(__file__).parent.parent / "prompts")


async def generate_node(state: SingleQuestionState) -> dict:
    """Generate a question based on the configuration.

    This node:
    1. Renders the generation prompt with ai-prompter
    2. Invokes the generator model
    3. Parses the response into a Question model
    4. Handles validation errors with retry logic

    Args:
        state: Current flow state containing config and any previous attempts

    Returns:
        Dict with updated state fields (current_question, error, retry_count)
    """
    config = state.config
    parser = PydanticOutputParser(pydantic_object=Question)

    # Build prompt context
    prompt_context = {
        "question_type": config.question_type.value,
        "content": config.content,
        "topic": config.topic,
        "language": config.language,
        "generator_instructions": config.generator_instructions,
        "format_instructions": parser.get_format_instructions(),
        "supervisor_feedback": state.supervisor_feedback,
    }

    # Render the prompt
    prompter = Prompter(prompt_template="generate_question", prompt_dir=PROMPTS_DIR)
    prompt = prompter.render(prompt_context)

    try:
        # Invoke the model
        response = await config.generator_model.ainvoke(prompt)

        # Extract content from response
        content = response.content if hasattr(response, "content") else str(response)

        # Parse the response
        question = parser.parse(content)

        return {
            "current_question": question,
            "error": None,
        }

    except Exception as e:
        # Handle validation or other errors
        error_msg = str(e)

        # Check if we should retry
        if config.retry_on_validation_error and state.retry_count < config.max_retries:
            return {
                "error": error_msg,
                "retry_count": state.retry_count + 1,
            }

        # Max retries reached or retry disabled
        return {
            "error": error_msg,
            "current_question": None,
        }
