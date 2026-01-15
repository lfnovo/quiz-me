"""Tests for quiz-me models."""

import pytest
from pydantic import ValidationError

from quiz_me.models import (
    GenerationError,
    GenerationResult,
    MultiGenerationResult,
    Question,
    QuestionPlan,
    QuestionSpec,
    QuestionType,
    SupervisionResult,
)


class TestQuestionType:
    def test_enum_values(self):
        assert QuestionType.MULTIPLE_CHOICE.value == "multiple_choice"
        assert QuestionType.OPEN_ENDED.value == "open_ended"
        assert QuestionType.FILL_IN_THE_BLANK.value == "fill_in_the_blank"


class TestQuestion:
    def test_valid_multiple_choice(self):
        q = Question(
            statement="What is the capital of France? This is a longer question.",
            question_type=QuestionType.MULTIPLE_CHOICE,
            alternatives=["Paris", "London", "Berlin", "Madrid"],
            correct_answer="Paris",
            explanation="Paris is the capital of France. It has been the capital since the 10th century.",
        )
        assert q.statement == "What is the capital of France? This is a longer question."
        assert q.question_type == QuestionType.MULTIPLE_CHOICE
        assert len(q.alternatives) == 4
        assert q.correct_answer == "Paris"
        assert q.approved is True

    def test_valid_open_ended(self):
        q = Question(
            statement="Explain the concept of recursion in programming in detail.",
            question_type=QuestionType.OPEN_ENDED,
            alternatives=None,
            correct_answer=None,
            explanation="Recursion is a programming technique where a function calls itself to solve smaller subproblems.",
        )
        assert q.alternatives is None
        assert q.correct_answer is None

    def test_valid_fill_in_the_blank(self):
        q = Question(
            statement="The _____ is the largest organ in the human body. Fill in the blank.",
            question_type=QuestionType.FILL_IN_THE_BLANK,
            alternatives=["Skin", "Liver", "Brain"],
            correct_answer="Skin",
            explanation="The skin is the largest organ in the human body, covering an average area of 2 square meters.",
        )
        assert q.alternatives == ["Skin", "Liver", "Brain"]
        assert q.correct_answer == "Skin"

    def test_statement_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            Question(
                statement="Too short",
                question_type=QuestionType.MULTIPLE_CHOICE,
                alternatives=["A", "B", "C"],
                correct_answer="A",
                explanation="This is a valid explanation that is long enough.",
            )
        assert "at least 20 characters" in str(exc_info.value)

    def test_multiple_choice_requires_alternatives(self):
        with pytest.raises(ValidationError) as exc_info:
            Question(
                statement="What is the capital of France? This is a longer question.",
                question_type=QuestionType.MULTIPLE_CHOICE,
                alternatives=None,
                correct_answer="Paris",
                explanation="Paris is the capital of France. It has been the capital since the 10th century.",
            )
        assert "must have alternatives" in str(exc_info.value)

    def test_multiple_choice_requires_correct_answer(self):
        with pytest.raises(ValidationError) as exc_info:
            Question(
                statement="What is the capital of France? This is a longer question.",
                question_type=QuestionType.MULTIPLE_CHOICE,
                alternatives=["Paris", "London", "Berlin"],
                correct_answer=None,
                explanation="Paris is the capital of France. It has been the capital since the 10th century.",
            )
        assert "must have a correct_answer" in str(exc_info.value)

    def test_multiple_choice_correct_answer_must_be_in_alternatives(self):
        with pytest.raises(ValidationError) as exc_info:
            Question(
                statement="What is the capital of France? This is a longer question.",
                question_type=QuestionType.MULTIPLE_CHOICE,
                alternatives=["Paris", "London", "Berlin"],
                correct_answer="Rome",
                explanation="Paris is the capital of France. It has been the capital since the 10th century.",
            )
        assert "must be one of the alternatives" in str(exc_info.value)

    def test_open_ended_must_not_have_alternatives(self):
        with pytest.raises(ValidationError) as exc_info:
            Question(
                statement="Explain the concept of recursion in programming in detail.",
                question_type=QuestionType.OPEN_ENDED,
                alternatives=["Option A", "Option B", "Option C"],
                correct_answer=None,
                explanation="Recursion is a programming technique where a function calls itself to solve smaller subproblems.",
            )
        assert "Open-ended questions must have alternatives set to None" in str(exc_info.value)

    def test_alternatives_too_few(self):
        with pytest.raises(ValidationError) as exc_info:
            Question(
                statement="What is the capital of France? This is a longer question.",
                question_type=QuestionType.MULTIPLE_CHOICE,
                alternatives=["Paris", "London"],
                correct_answer="Paris",
                explanation="Paris is the capital of France. It has been the capital since the 10th century.",
            )
        assert "at least 3 alternatives" in str(exc_info.value)

    def test_alternatives_too_many(self):
        with pytest.raises(ValidationError) as exc_info:
            Question(
                statement="What is the capital of France? This is a longer question.",
                question_type=QuestionType.MULTIPLE_CHOICE,
                alternatives=["Paris", "London", "Berlin", "Madrid", "Rome", "Vienna"],
                correct_answer="Paris",
                explanation="Paris is the capital of France. It has been the capital since the 10th century.",
            )
        assert "at most 5 alternatives" in str(exc_info.value)

    def test_alternatives_must_be_unique(self):
        with pytest.raises(ValidationError) as exc_info:
            Question(
                statement="What is the capital of France? This is a longer question.",
                question_type=QuestionType.MULTIPLE_CHOICE,
                alternatives=["Paris", "Paris", "Berlin"],
                correct_answer="Paris",
                explanation="Paris is the capital of France. It has been the capital since the 10th century.",
            )
        assert "must be unique" in str(exc_info.value)

    def test_difficulty_valid_range(self):
        q = Question(
            statement="What is the capital of France? This is a longer question.",
            question_type=QuestionType.MULTIPLE_CHOICE,
            alternatives=["Paris", "London", "Berlin"],
            correct_answer="Paris",
            explanation="Paris is the capital of France. It has been the capital since the 10th century.",
            difficulty=0.5,
        )
        assert q.difficulty == 0.5

    def test_difficulty_invalid_range(self):
        with pytest.raises(ValidationError):
            Question(
                statement="What is the capital of France? This is a longer question.",
                question_type=QuestionType.MULTIPLE_CHOICE,
                alternatives=["Paris", "London", "Berlin"],
                correct_answer="Paris",
                explanation="Paris is the capital of France. It has been the capital since the 10th century.",
                difficulty=1.5,
            )


class TestQuestionSpec:
    def test_valid_spec(self):
        spec = QuestionSpec(
            question_type=QuestionType.MULTIPLE_CHOICE,
            focus_area="Capital cities of Europe",
            guidance="Focus on major capitals",
        )
        assert spec.question_type == QuestionType.MULTIPLE_CHOICE
        assert spec.focus_area == "Capital cities of Europe"
        assert spec.guidance == "Focus on major capitals"

    def test_spec_without_guidance(self):
        spec = QuestionSpec(
            question_type=QuestionType.OPEN_ENDED,
            focus_area="Programming concepts",
        )
        assert spec.guidance is None


class TestQuestionPlan:
    def test_valid_plan(self):
        plan = QuestionPlan(
            total_questions=2,
            question_specs=[
                QuestionSpec(question_type=QuestionType.MULTIPLE_CHOICE, focus_area="Topic 1"),
                QuestionSpec(question_type=QuestionType.OPEN_ENDED, focus_area="Topic 2"),
            ],
        )
        assert plan.total_questions == 2
        assert len(plan.question_specs) == 2

    def test_plan_count_mismatch(self):
        with pytest.raises(ValidationError) as exc_info:
            QuestionPlan(
                total_questions=3,
                question_specs=[
                    QuestionSpec(question_type=QuestionType.MULTIPLE_CHOICE, focus_area="Topic 1"),
                    QuestionSpec(question_type=QuestionType.OPEN_ENDED, focus_area="Topic 2"),
                ],
            )
        assert "must match total_questions" in str(exc_info.value)


class TestSupervisionResult:
    def test_approved_result(self):
        result = SupervisionResult(
            approved=True,
            feedback="Question meets all quality criteria.",
        )
        assert result.approved is True
        assert result.severity is None

    def test_rejected_result(self):
        result = SupervisionResult(
            approved=False,
            feedback="Question is ambiguous.",
            severity="major",
        )
        assert result.approved is False
        assert result.severity == "major"

    def test_severity_cleared_when_approved(self):
        result = SupervisionResult(
            approved=True,
            feedback="Good question.",
            severity="minor",
        )
        assert result.severity is None


class TestGenerationResult:
    def test_valid_result(self):
        q = Question(
            statement="What is the capital of France? This is a longer question.",
            question_type=QuestionType.MULTIPLE_CHOICE,
            alternatives=["Paris", "London", "Berlin"],
            correct_answer="Paris",
            explanation="Paris is the capital of France. It has been the capital since the 10th century.",
        )
        result = GenerationResult(
            question=q,
            retries_used=1,
            generation_time_ms=500,
        )
        assert result.question == q
        assert result.retries_used == 1
        assert result.generation_time_ms == 500


class TestMultiGenerationResult:
    def test_valid_result(self):
        q = Question(
            statement="What is the capital of France? This is a longer question.",
            question_type=QuestionType.MULTIPLE_CHOICE,
            alternatives=["Paris", "London", "Berlin"],
            correct_answer="Paris",
            explanation="Paris is the capital of France. It has been the capital since the 10th century.",
        )
        plan = QuestionPlan(
            total_questions=1,
            question_specs=[QuestionSpec(question_type=QuestionType.MULTIPLE_CHOICE, focus_area="Geography")],
        )
        result = MultiGenerationResult(
            questions=[q],
            plan=plan,
            total_retries_used=0,
            generation_time_ms=1000,
        )
        assert len(result.questions) == 1
        assert result.plan == plan


class TestGenerationError:
    def test_error_creation(self):
        error = GenerationError(
            message="Failed to generate question",
            last_attempt=None,
            retry_count=3,
        )
        assert str(error) == "Failed to generate question"
        assert error.retry_count == 3

    def test_error_with_original(self):
        original = ValueError("Invalid response")
        error = GenerationError(
            message="Failed to parse response",
            last_attempt=None,
            retry_count=1,
            original_error=original,
        )
        assert error.original_error == original
