"""Tests for quiz-me configuration classes."""

import pytest
from pydantic import ValidationError
from unittest.mock import MagicMock

from quiz_me.config import (
    BaseGeneratorConfig,
    MultiQuestionConfig,
    QuestionTypeMix,
    SingleQuestionConfig,
)
from quiz_me.models import QuestionType


class TestQuestionTypeMix:
    def test_valid_mix(self):
        mix = QuestionTypeMix(
            question_type=QuestionType.MULTIPLE_CHOICE,
            count=3,
        )
        assert mix.question_type == QuestionType.MULTIPLE_CHOICE
        assert mix.count == 3

    def test_count_must_be_positive(self):
        with pytest.raises(ValidationError):
            QuestionTypeMix(
                question_type=QuestionType.MULTIPLE_CHOICE,
                count=0,
            )


class TestSingleQuestionConfig:
    def test_valid_config_with_content(self):
        model = MagicMock()
        config = SingleQuestionConfig(
            content="This is the content to generate questions from.",
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=model,
        )
        assert config.content == "This is the content to generate questions from."
        assert config.topic is None
        assert config.question_type == QuestionType.MULTIPLE_CHOICE

    def test_valid_config_with_topic(self):
        model = MagicMock()
        config = SingleQuestionConfig(
            topic="Python programming basics",
            question_type=QuestionType.OPEN_ENDED,
            generator_model=model,
        )
        assert config.topic == "Python programming basics"
        assert config.content is None

    def test_requires_content_or_topic(self):
        model = MagicMock()
        with pytest.raises(ValidationError) as exc_info:
            SingleQuestionConfig(
                question_type=QuestionType.MULTIPLE_CHOICE,
                generator_model=model,
            )
        assert "content" in str(exc_info.value) or "topic" in str(exc_info.value)

    def test_content_and_topic_mutually_exclusive(self):
        model = MagicMock()
        with pytest.raises(ValidationError) as exc_info:
            SingleQuestionConfig(
                content="Some content",
                topic="Some topic",
                question_type=QuestionType.MULTIPLE_CHOICE,
                generator_model=model,
            )
        assert "mutually exclusive" in str(exc_info.value)

    def test_supervision_requires_supervisor_model(self):
        model = MagicMock()
        with pytest.raises(ValidationError) as exc_info:
            SingleQuestionConfig(
                content="Some content",
                question_type=QuestionType.MULTIPLE_CHOICE,
                generator_model=model,
                supervision_enabled=True,
            )
        assert "supervisor_model" in str(exc_info.value)

    def test_supervision_with_supervisor_model(self):
        gen_model = MagicMock()
        sup_model = MagicMock()
        config = SingleQuestionConfig(
            content="Some content",
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=gen_model,
            supervisor_model=sup_model,
            supervision_enabled=True,
        )
        assert config.supervision_enabled is True
        assert config.supervisor_model == sup_model

    def test_custom_instructions(self):
        model = MagicMock()
        config = SingleQuestionConfig(
            content="Medical content",
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=model,
            generator_instructions="Focus on pharmacology terminology",
            supervisor_instructions="Verify medical accuracy",
        )
        assert config.generator_instructions == "Focus on pharmacology terminology"
        assert config.supervisor_instructions == "Verify medical accuracy"

    def test_default_values(self):
        model = MagicMock()
        config = SingleQuestionConfig(
            content="Some content",
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=model,
        )
        assert config.max_retries == 3
        assert config.retry_on_validation_error is True
        assert config.supervision_enabled is False
        assert config.language is None

    def test_language_property(self):
        model = MagicMock()
        config = SingleQuestionConfig(
            content="Some content",
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=model,
            language="Portuguese",
        )
        assert config.language == "Portuguese"


class TestMultiQuestionConfig:
    def test_valid_config(self):
        model = MagicMock()
        config = MultiQuestionConfig(
            content="Some educational content.",
            num_questions=5,
            generator_model=model,
        )
        assert config.num_questions == 5
        assert config.question_mix is None

    def test_valid_config_with_mix(self):
        model = MagicMock()
        config = MultiQuestionConfig(
            content="Some educational content.",
            num_questions=5,
            question_mix=[
                QuestionTypeMix(question_type=QuestionType.MULTIPLE_CHOICE, count=3),
                QuestionTypeMix(question_type=QuestionType.OPEN_ENDED, count=2),
            ],
            generator_model=model,
        )
        assert len(config.question_mix) == 2
        assert config.question_mix[0].count == 3
        assert config.question_mix[1].count == 2

    def test_question_mix_count_must_match(self):
        model = MagicMock()
        with pytest.raises(ValidationError) as exc_info:
            MultiQuestionConfig(
                content="Some educational content.",
                num_questions=5,
                question_mix=[
                    QuestionTypeMix(question_type=QuestionType.MULTIPLE_CHOICE, count=2),
                    QuestionTypeMix(question_type=QuestionType.OPEN_ENDED, count=2),
                ],
                generator_model=model,
            )
        assert "must equal num_questions" in str(exc_info.value)

    def test_num_questions_must_be_positive(self):
        model = MagicMock()
        with pytest.raises(ValidationError):
            MultiQuestionConfig(
                content="Some content",
                num_questions=0,
                generator_model=model,
            )

    def test_planning_instructions(self):
        model = MagicMock()
        config = MultiQuestionConfig(
            content="Some content",
            num_questions=3,
            generator_model=model,
            planning_instructions="Focus on key concepts only",
        )
        assert config.planning_instructions == "Focus on key concepts only"

    def test_inherits_from_base(self):
        model = MagicMock()
        sup_model = MagicMock()
        config = MultiQuestionConfig(
            content="Some content",
            num_questions=3,
            generator_model=model,
            supervisor_model=sup_model,
            supervision_enabled=True,
            max_retries=5,
        )
        assert config.max_retries == 5
        assert config.supervision_enabled is True
