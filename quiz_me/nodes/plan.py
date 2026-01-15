"""Question planning node for Langgraph flows."""

from pathlib import Path

from ai_prompter import Prompter
from langchain_core.output_parsers import PydanticOutputParser

from quiz_me.models import QuestionPlan
from quiz_me.states import MultiQuestionState

# Prompts directory for ai-prompter
PROMPTS_DIR = str(Path(__file__).parent.parent / "prompts")


async def plan_node(state: MultiQuestionState) -> dict:
    """Create a plan for generating multiple questions.

    This node:
    1. Analyzes the content/topic and requirements
    2. Creates a plan specifying each question's focus and type
    3. Returns the plan for subsequent generation

    Args:
        state: Current flow state containing config

    Returns:
        Dict with updated state fields (plan)
    """
    config = state.config
    parser = PydanticOutputParser(pydantic_object=QuestionPlan)

    # Build prompt context
    prompt_context = {
        "content": config.content,
        "topic": config.topic,
        "language": config.language,
        "num_questions": config.num_questions,
        "question_mix": [
            {"question_type": mix.question_type.value, "count": mix.count}
            for mix in config.question_mix
        ] if config.question_mix else None,
        "planning_instructions": config.planning_instructions,
        "generator_instructions": config.generator_instructions,
        "format_instructions": parser.get_format_instructions(),
    }

    # Render the prompt
    prompter = Prompter(prompt_template="plan_questions", prompt_dir=PROMPTS_DIR)
    prompt = prompter.render(prompt_context)

    try:
        # Invoke the model
        response = await config.generator_model.ainvoke(prompt)

        # Extract content from response
        content = response.content if hasattr(response, "content") else str(response)

        # Parse the response
        plan = parser.parse(content)

        return {
            "plan": plan,
        }

    except Exception as e:
        # If planning fails, create a simple default plan
        from quiz_me.models import QuestionSpec, QuestionType

        # Determine question types to use
        if config.question_mix:
            specs = []
            for mix in config.question_mix:
                for i in range(mix.count):
                    specs.append(
                        QuestionSpec(
                            question_type=mix.question_type,
                            focus_area=f"Aspect {len(specs) + 1} of the content",
                            guidance=None,
                        )
                    )
        else:
            # Default to all multiple choice
            specs = [
                QuestionSpec(
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    focus_area=f"Aspect {i + 1} of the content",
                    guidance=None,
                )
                for i in range(config.num_questions)
            ]

        fallback_plan = QuestionPlan(
            total_questions=config.num_questions,
            question_specs=specs,
        )

        return {
            "plan": fallback_plan,
        }
