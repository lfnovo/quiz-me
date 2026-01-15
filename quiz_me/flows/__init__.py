"""Langgraph flows for question generation."""

from quiz_me.flows.multi import multi_question_flow
from quiz_me.flows.single import single_question_flow

__all__ = [
    "single_question_flow",
    "multi_question_flow",
]
