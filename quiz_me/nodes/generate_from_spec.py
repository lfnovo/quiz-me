"""Question generation from spec node for multi-question flows."""

from pathlib import Path

from ai_prompter import Prompter
from langchain_core.output_parsers import PydanticOutputParser

from quiz_me.models import Question
from quiz_me.states import MultiQuestionState

# Prompts directory for ai-prompter
PROMPTS_DIR = str(Path(__file__).parent.parent / "prompts")


async def generate_from_spec_node(state: MultiQuestionState) -> dict:
    """Generate a question based on a spec from the plan.

    This node:
    1. Gets the current spec from the plan based on current_index
    2. Renders the generation prompt with spec details
    3. Invokes the generator model
    4. Parses the response into a Question model

    Args:
        state: Current flow state containing config, plan, and current index

    Returns:
        Dict with updated state fields (current_question, error, current_retry_count)
    """
    config = state.config
    plan = state.plan

    if plan is None:
        return {
            "error": "No plan available - planning phase failed",
        }

    if state.current_index >= len(plan.question_specs):
        return {
            "error": f"Invalid index {state.current_index} for plan with {len(plan.question_specs)} specs",
        }

    # Get the current spec
    spec = plan.question_specs[state.current_index]

    parser = PydanticOutputParser(pydantic_object=Question)

    # Build prompt context
    prompt_context = {
        "question_type": spec.question_type.value,
        "content": config.content,
        "topic": config.topic,
        "language": config.language,
        "generator_instructions": config.generator_instructions,
        "focus_area": spec.focus_area,
        "spec_guidance": spec.guidance,
        "format_instructions": parser.get_format_instructions(),
        "supervisor_feedback": state.current_supervisor_feedback,
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
        if config.retry_on_validation_error and state.current_retry_count < config.max_retries:
            return {
                "error": error_msg,
                "current_retry_count": state.current_retry_count + 1,
                "total_retries": state.total_retries + 1,
            }

        # Max retries reached or retry disabled
        return {
            "error": error_msg,
            "current_question": None,
        }
