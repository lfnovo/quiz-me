# Flows

Langgraph flow definitions (state graphs) that orchestrate question generation.

## Files

- **`single.py`**: Single question generation flow. Graph: START → generate → (supervise if enabled) → retry loop → END. Uses SingleQuestionState.
- **`multi.py`**: Multi-question generation flow. Graph: START → plan → generate loop (with optional supervision per question) → finalize → END. Uses MultiQuestionState.
- **`__init__.py`**: Exports compiled flows.

## Patterns

- **Graph Construction**: Use `StateGraph(StateModel)` to create graph with Pydantic state schema.
- **Node Registration**: `graph.add_node("name", node_function)` registers nodes.
- **Edge Types**:
  - `graph.add_edge(START, "node")` - unconditional edge
  - `graph.add_conditional_edges("node", router_func, {"route1": "node1", ...})` - conditional routing
- **Router Functions**: Pure functions that take state and return string literal matching edge dict keys. Type as `Literal["route1", "route2", ...]`.
- **Compilation**: `graph.compile()` returns executable flow. Compiled flow stored in module-level variable (e.g., `single_question_flow`).
- **Invocation**: Flows invoked with `await flow.ainvoke(initial_state, {"recursion_limit": 50})`. Higher recursion limit needed for supervision retry loops.

## Integration

- Imports from: `nodes/` (node functions), `states.py` (state models)
- Used by: `__init__.py` (public API functions)
- Data flow: Public API creates initial state → invokes flow → flow returns final state dict/object → public API extracts results

## Flow Details

### Single Question Flow

Conditional logic:
- **After generate**: Routes to "supervise" if enabled and question generated, "retry" if error and retries available, "end" otherwise.
- **After supervise**: Routes to "generate" if rejected and retries available, "end" if approved or max retries.

State fields used: `current_question`, `supervision_result`, `supervisor_feedback`, `retry_count`, `error`, `config`

### Multi Question Flow

Conditional logic:
- **After generate**: Routes to "supervise" if enabled and question exists, "finalize" otherwise.
- **After supervise**: Routes to "generate" if rejected and retries available, "finalize" if approved or max retries.
- **After finalize**: Routes to "generate" if `current_index < len(plan.question_specs)`, "end" when all questions complete.

State fields used: `plan`, `questions`, `current_index`, `current_question`, `current_supervision_result`, `current_supervisor_feedback`, `current_retry_count`, `total_retries`, `error`, `config`

## Gotchas

- **Recursion Limit**: Default Langgraph limit (25) insufficient for supervision retry loops. Public API uses `{"recursion_limit": 50}` in ainvoke config.
- **Return Type Ambiguity**: Langgraph can return state as dict or Pydantic object depending on version/config. Public API handles both with `isinstance(final_state, dict)` checks.
- **Router Typing**: Router functions must return Literal type matching edge dictionary keys exactly, not plain string.
- **Multi-Flow Index Management**: `current_index` incremented by finalize_question_node, not by generate_from_spec_node. This ensures index only advances when question is finalized.
- **State Mutation**: Nodes return dicts that Langgraph merges into state. List fields (like `questions`) must be explicitly copied (`list(state.questions)`) before appending to avoid in-place mutation issues.

## When Adding Flows

- Choose appropriate state model (or create new one in states.py)
- Define router functions with Literal return types before graph construction
- Use descriptive node names in graph (they appear in traces/logs)
- Set appropriate recursion_limit when compiling/invoking
- Export compiled flow from `__init__.py`
- Handle both dict and Pydantic object returns in calling code
