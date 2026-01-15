"""Finalize question node for multi-question flows."""

from quiz_me.models import Question
from quiz_me.states import MultiQuestionState


async def finalize_question_node(state: MultiQuestionState) -> dict:
    """Finalize the current question and prepare for the next one.

    This node:
    1. Adds the current question to the questions list (with supervision status)
    2. Resets current question tracking state
    3. Increments the current index

    Args:
        state: Current flow state

    Returns:
        Dict with updated state fields
    """
    current_question = state.current_question

    if current_question is None:
        # No question to finalize - this shouldn't happen but handle gracefully
        return {
            "current_index": state.current_index + 1,
            "current_question": None,
            "current_supervision_result": None,
            "current_retry_count": 0,
            "current_supervisor_feedback": None,
        }

    # Update question with supervision status if applicable
    if state.current_supervision_result is not None:
        final_question = Question(
            statement=current_question.statement,
            question_type=current_question.question_type,
            alternatives=current_question.alternatives,
            correct_answer=current_question.correct_answer,
            explanation=current_question.explanation,
            difficulty=current_question.difficulty,
            approved=state.current_supervision_result.approved,
            supervision_feedback=(
                state.current_supervision_result.feedback
                if not state.current_supervision_result.approved
                else None
            ),
        )
    else:
        final_question = current_question

    # Add to questions list
    updated_questions = list(state.questions)
    updated_questions.append(final_question)

    return {
        "questions": updated_questions,
        "current_index": state.current_index + 1,
        "current_question": None,
        "current_supervision_result": None,
        "current_retry_count": 0,
        "current_supervisor_feedback": None,
    }
