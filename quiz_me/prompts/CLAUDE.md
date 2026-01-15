# Prompts

Jinja templates for LLM prompts used throughout the flows.

## Files

- **`generate_question.jinja`**: Generation prompt for creating questions. Handles multiple question types, optional focus area/guidance for multi-question flows, and supervisor feedback for retries.
- **`plan_questions.jinja`**: Planning prompt for multi-question generation. Analyzes content/topic and creates a QuestionPlan with focus areas and types.
- **`supervise_question.jinja`**: Supervision prompt for reviewing generated questions. Evaluates quality and provides structured feedback.
- **`_quality_guidelines.jinja`**: Partial template with quality criteria. Included by other prompts to ensure consistent quality standards.

## Patterns

- **Prompt Rendering**: All nodes use `ai_prompter.Prompter` with `prompt_dir=PROMPTS_DIR` (never rely on env var). Pass `PROMPTS_DIR = str(Path(__file__).parent.parent / "prompts")` from nodes.
- **Template Context**: Each template expects specific context variables (content/topic, language, format_instructions from Pydantic parser, optional custom instructions).
- **Conditional Sections**: Templates use Jinja conditionals for optional fields (supervisor_feedback, focus_area, spec_guidance, question_mix).
- **Structured Output**: All prompts include `format_instructions` from `PydanticOutputParser` to ensure JSON responses that validate against models.

## Gotchas

- Always pass `prompt_dir` explicitly to Prompter - don't rely on PROMPTS_DIR environment variable.
- The `_quality_guidelines.jinja` file is a Jinja partial (starts with `_`), not a standalone prompt template.
- `generate_question.jinja` is used for both single generation and multi-question generation (differentiated by presence of `focus_area` and `spec_guidance` variables).
- Supervisor feedback is passed through `supervisor_feedback` context variable when retrying after rejection.

## When Adding Prompts

- Follow naming convention: `{action}_{object}.jinja` (e.g., `generate_question.jinja`).
- Include `format_instructions` in context for structured outputs.
- Use conditionals for optional sections rather than creating separate templates.
- Consider extracting common quality/style guidelines to partials.
