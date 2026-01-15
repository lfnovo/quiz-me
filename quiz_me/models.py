"""Pydantic models for quiz-me library."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class QuestionType(str, Enum):
    """Type of question to generate."""

    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_ENDED = "open_ended"
    FILL_IN_THE_BLANK = "fill_in_the_blank"


class Question(BaseModel):
    """Represents a generated question with all its components."""

    statement: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="The question text/prompt",
    )
    question_type: QuestionType = Field(
        ...,
        description="The type of question",
    )
    alternatives: list[str] | None = Field(
        default=None,
        description="Answer options. Required for MULTIPLE_CHOICE and FILL_IN_THE_BLANK (3-5 items), must be None for OPEN_ENDED",
    )
    correct_answer: str | None = Field(
        default=None,
        description="The correct answer. Required for MULTIPLE_CHOICE and FILL_IN_THE_BLANK. "
        "For OPEN_ENDED, this contains the grading rubric/expected answer criteria.",
    )
    explanation: str = Field(
        ...,
        min_length=50,
        max_length=1200,
        description="Educational explanation of the answer",
    )
    difficulty: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional difficulty level (0.0-1.0 scale)",
    )
    approved: bool = Field(
        default=True,
        description="Supervision approval status. Defaults to True if no supervision.",
    )
    supervision_feedback: str | None = Field(
        default=None,
        description="Feedback from supervisor if rejected/approved with comments",
    )

    @field_validator("alternatives")
    @classmethod
    def validate_alternatives(
        cls, v: list[str] | None, info
    ) -> list[str] | None:
        """Validate alternatives based on question type."""
        question_type = info.data.get("question_type")

        if question_type == QuestionType.OPEN_ENDED:
            if v is not None:
                raise ValueError(
                    "Open-ended questions must have alternatives set to None"
                )
            return None

        if question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.FILL_IN_THE_BLANK):
            if v is None:
                raise ValueError(
                    f"{question_type.value} questions must have alternatives"
                )
            if len(v) < 3:
                raise ValueError(
                    f"{question_type.value} questions must have at least 3 alternatives"
                )
            if len(v) > 5:
                raise ValueError(
                    f"{question_type.value} questions must have at most 5 alternatives"
                )
            if len(v) != len(set(v)):
                raise ValueError("All alternatives must be unique")

        return v

    @field_validator("correct_answer")
    @classmethod
    def validate_correct_answer(cls, v: str | None, info) -> str | None:
        """Validate correct_answer based on question type."""
        question_type = info.data.get("question_type")
        alternatives = info.data.get("alternatives")

        if question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.FILL_IN_THE_BLANK):
            if v is None:
                raise ValueError(
                    f"{question_type.value} questions must have a correct_answer"
                )
            if alternatives and v not in alternatives:
                raise ValueError(
                    f"correct_answer '{v}' must be one of the alternatives: {alternatives}"
                )

        return v


class QuestionSpec(BaseModel):
    """Specification for a single question within a plan."""

    question_type: QuestionType = Field(
        ...,
        description="Type of question to generate",
    )
    focus_area: str = Field(
        ...,
        description="What aspect of the content this question should cover",
    )
    guidance: str | None = Field(
        default=None,
        description="Additional guidance for generating this specific question",
    )


class QuestionPlan(BaseModel):
    """Planning output for multi-question generation."""

    total_questions: int = Field(
        ...,
        ge=1,
        description="Number of questions to generate",
    )
    question_specs: list[QuestionSpec] = Field(
        ...,
        description="Specifications for each question",
    )

    @model_validator(mode="after")
    def validate_specs_count(self) -> "QuestionPlan":
        """Ensure question_specs count matches total_questions."""
        if len(self.question_specs) != self.total_questions:
            raise ValueError(
                f"question_specs count ({len(self.question_specs)}) must match "
                f"total_questions ({self.total_questions})"
            )
        return self


class SupervisionResult(BaseModel):
    """Result from the supervision node."""

    approved: bool = Field(
        ...,
        description="Whether the question is approved",
    )
    feedback: str = Field(
        ...,
        description="Explanation of the decision or improvement suggestions",
    )
    severity: Literal["minor", "major", "critical"] | None = Field(
        default=None,
        description="Severity level - only relevant when not approved",
    )

    @model_validator(mode="after")
    def validate_severity(self) -> "SupervisionResult":
        """Severity should only be set when not approved."""
        if self.approved and self.severity is not None:
            # Clear severity if approved
            object.__setattr__(self, "severity", None)
        return self


class GenerationResult(BaseModel):
    """Result from question generation (includes metadata)."""

    question: Question = Field(
        ...,
        description="The generated question",
    )
    retries_used: int = Field(
        default=0,
        ge=0,
        description="Number of retries that were needed",
    )
    generation_time_ms: int = Field(
        default=0,
        ge=0,
        description="Time taken to generate (milliseconds)",
    )


class MultiGenerationResult(BaseModel):
    """Result from multi-question generation."""

    questions: list[Question] = Field(
        ...,
        description="Generated questions",
    )
    plan: QuestionPlan = Field(
        ...,
        description="The plan that was executed",
    )
    total_retries_used: int = Field(
        default=0,
        ge=0,
        description="Total retries across all questions",
    )
    generation_time_ms: int = Field(
        default=0,
        ge=0,
        description="Total time taken (milliseconds)",
    )


class GenerationError(Exception):
    """Raised when question generation fails."""

    def __init__(
        self,
        message: str,
        last_attempt: Question | None = None,
        retry_count: int = 0,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.last_attempt = last_attempt
        self.retry_count = retry_count
        self.original_error = original_error

    def __str__(self) -> str:
        return self.message
