# Nodes

Langgraph node functions that implement question generation, supervision, planning, and state management.

## Files

- **`generate.py`**: Single question generation node. Renders prompt, invokes generator model, parses into Question. Used in single-question flow.
- **`generate_from_spec.py`**: Multi-question generation node. Gets spec from plan based on `current_index`, then generates. Used in multi-question flow.
- **`supervise.py`**: Single question supervision node. Reviews question against quality criteria, returns SupervisionResult. Updates `supervision_result` and `supervisor_feedback` in state.
- **`supervise_multi.py`**: Multi-question supervision node. Same as supervise.py but updates `current_supervision_result` and `current_supervisor_feedback` for multi-question state tracking.
- **`plan.py`**: Planning node for multi-question generation. Creates QuestionPlan with specs for each question (type, focus_area, guidance). Has fallback to default plan if LLM planning fails.
- **`finalize_question.py`**: Multi-question finalization node. Adds current question to questions list (with supervision status), resets current tracking fields, increments index.
- **`improve.py`**: Standalone improvement function (not a flow node). Takes original question + feedback, regenerates improved version. Used by public `improve_question()` API.
- **`__init__.py`**: Exports all nodes.

## Patterns

- **Node Signature**: All flow nodes take state (Pydantic model) and return dict with state updates. Langgraph merges dict into state.
- **Async**: All nodes are async (`async def`) for LangChain model invocation compatibility.
- **Prompt Rendering**: All nodes use `Prompter(prompt_template="...", prompt_dir=PROMPTS_DIR)` where `PROMPTS_DIR = str(Path(__file__).parent.parent / "prompts")`.
- **Parser Pattern**: Nodes use `PydanticOutputParser(pydantic_object=Model)` to parse LLM JSON responses. `parser.get_format_instructions()` passed to prompt context.
- **Error Handling**: Try/except around model invocation. On exception, nodes return state updates with error info or increment retry counter if retries available.
- **Retry Logic**: Generate nodes check `config.retry_on_validation_error` and `state.retry_count < config.max_retries` before incrementing retry counter vs. marking as failed.
- **Supervision Feedback Loop**: When supervisor rejects, feedback stored in `supervisor_feedback` (single) or `current_supervisor_feedback` (multi) and passed to next generation attempt.

## Integration

- Used by: `flows/single.py`, `flows/multi.py`
- Imports from: `states.py` (state models), `models.py` (Question, SupervisionResult, QuestionPlan), `config.py` (config classes)
- Data flow: State enters node → node invokes LLM → parses response → returns state updates dict → Langgraph merges into state

## Gotchas

- **Return Dict, Not State**: Nodes must return plain dict with updated fields, not full state object. Langgraph handles merging.
- **State Type Mismatch**: `generate.py` and `supervise.py` use `SingleQuestionState`, while `generate_from_spec.py`, `supervise_multi.py`, `plan.py`, `finalize_question.py` use `MultiQuestionState`. Don't mix them.
- **PROMPTS_DIR Calculation**: Always use `str(Path(__file__).parent.parent / "prompts")` - this resolves to `quiz_me/prompts/` from `quiz_me/nodes/*.py`.
- **Fallback Plan**: `plan.py` has fallback logic if LLM planning fails - creates simple plan based on `question_mix` or defaults to all MULTIPLE_CHOICE.
- **Supervision Errors**: If supervision fails (exception), nodes treat it as rejection with critical severity rather than approving by default.
- **improve.py is Different**: `improve_question_node` is a standalone async function (not a flow node), called directly from public API, takes individual parameters not state.

## When Adding Nodes

- Accept state parameter (SingleQuestionState or MultiQuestionState)
- Return dict with state field updates (not full state object)
- Make async for LangChain compatibility
- Use PydanticOutputParser for structured outputs
- Handle exceptions gracefully - return error state updates rather than raising
- Follow naming: `{action}_node` or `{action}_{object}_node`
- Add to `__init__.py` exports
