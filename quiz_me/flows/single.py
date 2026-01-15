"""Single question generation flow using Langgraph."""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from quiz_me.nodes.generate import generate_node
from quiz_me.nodes.supervise import supervise_node
from quiz_me.states import SingleQuestionState


def should_supervise_or_retry(state: SingleQuestionState) -> Literal["supervise", "retry", "end"]:
    """Determine next step after generation.

    Routes to:
    - retry: If generation failed but retries are available
    - supervise: If supervision is enabled and question was generated
    - end: Otherwise
    """
    # If generation failed, check if we can retry
    if state.current_question is None:
        if state.error and state.retry_count < state.config.max_retries:
            return "retry"
        return "end"

    # If supervision is enabled, route to supervise
    if state.config.supervision_enabled:
        return "supervise"

    return "end"


def should_retry(state: SingleQuestionState) -> Literal["generate", "end"]:
    """Determine if generation should be retried after supervision.

    Routes to retry if:
    - Question was rejected by supervisor
    - Retry count is below max_retries
    """
    if state.supervision_result is None:
        return "end"

    if state.supervision_result.approved:
        return "end"

    # Check if we can retry
    if state.retry_count < state.config.max_retries:
        return "generate"

    return "end"


def build_single_question_graph() -> StateGraph:
    """Build the single question generation graph.

    Flow:
        START -> generate -> should_supervise_or_retry?
            -> (error, can retry) -> generate
            -> (no supervision) -> END
            -> (supervision) -> supervise -> should_retry?
                -> (approved) -> END
                -> (rejected, can retry) -> generate
                -> (rejected, max retries) -> END
    """
    # Create the graph with Pydantic state
    graph = StateGraph(SingleQuestionState)

    # Add nodes
    graph.add_node("generate", generate_node)
    graph.add_node("supervise", supervise_node)

    # Add edges
    graph.add_edge(START, "generate")

    # Conditional edge after generation
    graph.add_conditional_edges(
        "generate",
        should_supervise_or_retry,
        {
            "supervise": "supervise",
            "retry": "generate",
            "end": END,
        },
    )

    # Conditional edge after supervision
    graph.add_conditional_edges(
        "supervise",
        should_retry,
        {
            "generate": "generate",
            "end": END,
        },
    )

    return graph


# Build and compile the graph
single_question_graph = build_single_question_graph()
single_question_flow = single_question_graph.compile()
