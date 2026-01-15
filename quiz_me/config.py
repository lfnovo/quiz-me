"""Configuration classes for quiz-me library."""

from typing import Any

from pydantic import BaseModel, Field, model_validator

from quiz_me.models import QuestionType


class QuestionTypeMix(BaseModel):
    """Specifies distribution of question types for multi-question generation."""

    question_type: QuestionType = Field(
        ...,
        description="The type of question",
    )
    count: int = Field(
        ...,
        ge=1,
        description="Number of questions of this type to generate",
    )


class BaseGeneratorConfig(BaseModel):
    """Base configuration shared by all generation flows."""

    model_config = {"arbitrary_types_allowed": True}

    content: str | None = Field(
        default=None,
        description="Content text to generate questions from. Mutually exclusive with topic.",
    )
    topic: str | None = Field(
        default=None,
        description="Topic/concept for question generation (uses model knowledge). Mutually exclusive with content.",
    )
    generator_model: Any = Field(
        ...,
        description="LangChain-compatible model for generation",
    )
    supervisor_model: Any | None = Field(
        default=None,
        description="LangChain-compatible model for supervision. Required if supervision_enabled=True.",
    )
    supervision_enabled: bool = Field(
        default=False,
        description="Whether to enable supervision",
    )
    generator_instructions: str | None = Field(
        default=None,
        description="Domain-specific instructions for the generator",
    )
    supervisor_instructions: str | None = Field(
        default=None,
        description="Domain-specific instructions for the supervisor",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts for validation failures or supervision rejections",
    )
    retry_on_validation_error: bool = Field(
        default=True,
        description="Whether to retry when Pydantic validation fails",
    )
    language: str | None = Field(
        default=None,
        description="Language for generated content (e.g., 'Portuguese', 'English'). "
        "If not specified, defaults to English.",
    )

    @model_validator(mode="after")
    def validate_content_or_topic(self) -> "BaseGeneratorConfig":
        """Ensure exactly one of content or topic is provided."""
        if self.content is None and self.topic is None:
            raise ValueError("Either 'content' or 'topic' must be provided")
        if self.content is not None and self.topic is not None:
            raise ValueError(
                "'content' and 'topic' are mutually exclusive - provide only one"
            )
        return self

    @model_validator(mode="after")
    def validate_supervisor_model(self) -> "BaseGeneratorConfig":
        """Ensure supervisor_model is provided when supervision is enabled."""
        if self.supervision_enabled and self.supervisor_model is None:
            raise ValueError(
                "'supervisor_model' is required when 'supervision_enabled' is True"
            )
        return self


class SingleQuestionConfig(BaseGeneratorConfig):
    """Configuration for single question generation."""

    question_type: QuestionType = Field(
        ...,
        description="Type of question to generate",
    )


class MultiQuestionConfig(BaseGeneratorConfig):
    """Configuration for multi-question generation."""

    num_questions: int = Field(
        ...,
        ge=1,
        description="Total number of questions to generate",
    )
    question_mix: list[QuestionTypeMix] | None = Field(
        default=None,
        description="Distribution of question types. If None, planner decides.",
    )
    planning_instructions: str | None = Field(
        default=None,
        description="Additional instructions for the planning phase",
    )

    @model_validator(mode="after")
    def validate_question_mix_count(self) -> "MultiQuestionConfig":
        """Ensure question_mix counts sum to num_questions."""
        if self.question_mix is not None:
            total_count = sum(mix.count for mix in self.question_mix)
            if total_count != self.num_questions:
                raise ValueError(
                    f"Sum of question_mix counts ({total_count}) must equal "
                    f"num_questions ({self.num_questions})"
                )
        return self
