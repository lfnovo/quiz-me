# quiz-me

AI-powered question generation library using Langgraph flows.

## Architecture

This library orchestrates LLM-based question generation through Langgraph state machines with optional quality supervision.

### Core Files

- **`__init__.py`**: Public API functions (`generate_question`, `generate_questions`, `improve_question`). Wraps flows, handles timing, extracts results from final state.
- **`config.py`**: Pydantic config classes (`BaseGeneratorConfig`, `SingleQuestionConfig`, `MultiQuestionConfig`). Validates content/topic mutual exclusivity and supervision requirements.
- **`models.py`**: Pydantic models (`Question`, `QuestionType`, `QuestionPlan`, `QuestionSpec`, `SupervisionResult`, result models, `GenerationError`).
- **`states.py`**: Langgraph state schemas (`SingleQuestionState`, `MultiQuestionState`). Track generation progress, retries, supervision results.

### Submodules

- **[prompts/](prompts/CLAUDE.md)**: Jinja templates for LLM prompts (generation, planning, supervision).
- **[nodes/](nodes/CLAUDE.md)**: Langgraph node functions (generate, supervise, plan, finalize, improve).
- **[flows/](flows/CLAUDE.md)**: Langgraph flow definitions (single and multi-question state graphs).

## Data Flow

### Single Question
1. Public API creates `SingleQuestionState` from config
2. Flow: generate → (optional supervise → retry loop) → END
3. Extract `current_question` from final state, wrap in `GenerationResult`

### Multi Question
1. Public API creates `MultiQuestionState` from config
2. Flow: plan → (generate → optional supervise → finalize) loop → END
3. Extract `questions` and `plan` from final state, wrap in `MultiGenerationResult`

### Improvement
1. Public API calls `improve_question_node` directly (bypasses flow)
2. Node regenerates question with feedback context
3. Wrap in `GenerationResult`

## Key Patterns

- **Pydantic Everywhere**: Configs, states, models all use Pydantic for validation. Use `model_config = {"arbitrary_types_allowed": True}` for LangChain model fields.
- **State Updates as Dicts**: Nodes return plain dicts with updated fields, Langgraph merges into state. Never return full state object from node.
- **Prompt Rendering**: All prompts via `Prompter(prompt_template="...", prompt_dir=PROMPTS_DIR)`. Always pass `prompt_dir` explicitly, never rely on env var.
- **Structured Outputs**: Use `PydanticOutputParser` for all LLM responses. Pass `parser.get_format_instructions()` to prompt context.
- **Retry Logic**: Nodes check `config.max_retries` and increment `retry_count` on validation errors or supervision rejection.
- **Supervision Feedback Loop**: Rejected questions store feedback in state, passed to next generation attempt via prompt context.
- **Recursion Limit**: Flows invoked with `{"recursion_limit": 50}` to handle supervision retry loops (default 25 insufficient).
- **Final State Ambiguity**: Langgraph may return dict or Pydantic object. Public API checks `isinstance(final_state, dict)` and handles both.

## Gotchas

- **content/topic Mutual Exclusivity**: Config validation ensures exactly one is set. Don't pass both or neither.
- **Supervision Requires supervisor_model**: Config validation enforces this. If `supervision_enabled=True`, must provide `supervisor_model`.
- **Async Required**: All public API functions and node functions are async. Must use `await`.
- **Question Type Validation**: `Question` model validates alternatives/correct_answer based on question_type. OPEN_ENDED requires `alternatives=None`, MULTIPLE_CHOICE/FILL_IN_THE_BLANK require 3-5 alternatives with correct_answer in list.
- **State Type Mismatch**: Single-question flow uses `SingleQuestionState`, multi uses `MultiQuestionState`. Don't mix.
- **List Mutation**: When updating list fields in state (e.g., `questions`), explicitly copy (`list(state.questions)`) before appending to avoid mutation issues.
- **Fallback Plan**: Multi-question flow has fallback if planning fails - creates simple plan from `question_mix` or defaults to all MULTIPLE_CHOICE.
- **Supervision on Error**: If supervision itself fails, treated as rejection with critical severity (not default approval).

## Public API

- **`generate_question(SingleQuestionConfig)`** → `GenerationResult`: Generate single question with optional supervision.
- **`generate_questions(MultiQuestionConfig)`** → `MultiGenerationResult`: Generate multiple questions with planning and optional supervision.
- **`improve_question(Question, feedback, SingleQuestionConfig)`** → `GenerationResult`: Regenerate question incorporating feedback.

All functions async, raise `GenerationError` on failure.

## Configuration

See config.py:72-90 for validators, __init__.py:29-283 for usage examples in docstrings.

### Required
- One of `content` (text to generate from) or `topic` (concept using model knowledge)
- `generator_model` - LangChain-compatible model

### Optional
- `supervision_enabled` (default False) - requires `supervisor_model` if True
- `max_retries` (default 3) - retry attempts for validation/supervision failures
- `retry_on_validation_error` (default True) - retry on Pydantic errors
- `language` - target language (defaults to English if not specified)
- `generator_instructions` / `supervisor_instructions` - domain-specific instructions

### Multi-Question Only
- `num_questions` - total to generate
- `question_mix` - list of `QuestionTypeMix` (type + count), must sum to `num_questions`
- `planning_instructions` - additional planning guidance

## Testing

- Run tests: `uv run pytest tests/ -v`
- Live tests: `tests/test_live.py` (require real LLM API keys)
- Integration tests: `tests/test_integration.py`
- Unit tests: `tests/test_models.py`, `tests/test_config.py`, `tests/test_flows.py`

## When Modifying

- **Adding Question Type**: Update `QuestionType` enum in models.py, update validation in `Question.validate_alternatives` and `Question.validate_correct_answer`, update prompts.
- **Adding Config Option**: Add field to appropriate config class, update validators if constraints needed, update prompts if LLM needs to know about it.
- **Adding Node**: Create in nodes/, accept state param, return dict, make async, handle errors, add to nodes/__init__.py.
- **Modifying Flow**: Update flow definition in flows/, ensure router function return types match edge dict keys exactly (use Literal).
- **Changing Prompt**: Update Jinja template in prompts/, test with both content and topic modes, test with/without optional fields.
