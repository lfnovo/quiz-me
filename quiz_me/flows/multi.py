"""Multi-question generation flow using Langgraph."""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from quiz_me.nodes.finalize_question import finalize_question_node
from quiz_me.nodes.generate_from_spec import generate_from_spec_node
from quiz_me.nodes.plan import plan_node
from quiz_me.nodes.supervise_multi import supervise_multi_node
from quiz_me.states import MultiQuestionState


def should_supervise_multi(state: MultiQuestionState) -> Literal["supervise", "finalize"]:
    """Determine if supervision should be performed on current question.

    Routes to supervision if:
    - Supervision is enabled
    - A question was successfully generated
    """
    if not state.config.supervision_enabled:
        return "finalize"

    if state.current_question is None:
        return "finalize"

    return "supervise"


def should_retry_multi(state: MultiQuestionState) -> Literal["generate", "finalize"]:
    """Determine if generation should be retried after supervision.

    Routes to retry if:
    - Question was rejected by supervisor
    - Retry count is below max_retries
    """
    if state.current_supervision_result is None:
        return "finalize"

    if state.current_supervision_result.approved:
        return "finalize"

    # Check if we can retry
    if state.current_retry_count < state.config.max_retries:
        return "generate"

    return "finalize"


def should_continue(state: MultiQuestionState) -> Literal["generate", "end"]:
    """Determine if there are more questions to generate.

    Routes to generate if there are more specs in the plan.
    """
    if state.plan is None:
        return "end"

    if state.current_index < len(state.plan.question_specs):
        return "generate"

    return "end"


def build_multi_question_graph() -> StateGraph:
    """Build the multi-question generation graph.

    Flow:
        START -> plan -> generate -> should_supervise?
            -> (no supervision) -> finalize -> should_continue?
            -> (supervision) -> supervise -> should_retry?
                -> (approved) -> finalize -> should_continue?
                -> (rejected, can retry) -> generate
                -> (rejected, max retries) -> finalize -> should_continue?
        should_continue:
            -> (more questions) -> generate
            -> (all done) -> END
    """
    # Create the graph with Pydantic state
    graph = StateGraph(MultiQuestionState)

    # Add nodes
    graph.add_node("plan", plan_node)
    graph.add_node("generate", generate_from_spec_node)
    graph.add_node("supervise", supervise_multi_node)
    graph.add_node("finalize", finalize_question_node)

    # Add edges
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "generate")

    # Conditional edge after generation
    graph.add_conditional_edges(
        "generate",
        should_supervise_multi,
        {
            "supervise": "supervise",
            "finalize": "finalize",
        },
    )

    # Conditional edge after supervision
    graph.add_conditional_edges(
        "supervise",
        should_retry_multi,
        {
            "generate": "generate",
            "finalize": "finalize",
        },
    )

    # Conditional edge after finalize
    graph.add_conditional_edges(
        "finalize",
        should_continue,
        {
            "generate": "generate",
            "end": END,
        },
    )

    return graph


# Build and compile the graph
multi_question_graph = build_multi_question_graph()
multi_question_flow = multi_question_graph.compile()
