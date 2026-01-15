"""Integration tests for quiz-me library.

These tests exercise complete flows end-to-end, mirroring real-world usage
patterns from the testing notebook.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from quiz_me import (
    generate_question,
    generate_questions,
    improve_question,
    SingleQuestionConfig,
    MultiQuestionConfig,
    QuestionType,
    QuestionTypeMix,
    Question,
    GenerationError,
)


# =============================================================================
# Test Fixtures
# =============================================================================

SAMPLE_CONTENT = """
Python is a high-level, interpreted programming language known for its clear syntax
and readability. It was created by Guido van Rossum and first released in 1991.
Python supports multiple programming paradigms, including procedural, object-oriented,
and functional programming. It has a large standard library and an active community
that contributes thousands of third-party packages through PyPI (Python Package Index).
Python is widely used in web development, data science, machine learning, automation,
and scientific computing.
"""

PORTUGUESE_CONTENT = """
Python é uma linguagem de programação de alto nível, interpretada e de propósito geral.
Foi criada por Guido van Rossum e lançada pela primeira vez em 1991.
Python é conhecida por sua sintaxe clara e legível, sendo amplamente utilizada em
ciência de dados, inteligência artificial, desenvolvimento web e automação.
"""


def create_mock_model(response_content: str):
    """Create a mock LangChain model that returns the given content."""
    mock = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = response_content
    mock.ainvoke.return_value = mock_response
    return mock


def create_sequential_mock_model(responses: list[str]):
    """Create a mock model that returns different responses on each call."""
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        mock_response = MagicMock()
        mock_response.content = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return mock_response

    mock = AsyncMock()
    mock.ainvoke.side_effect = side_effect
    return mock


def valid_mc_question(
    statement: str = "What year was Python first released?",
    alternatives: list[str] | None = None,
    correct_answer: str | None = None,
    explanation: str = "Python was first released in 1991 by Guido van Rossum, making it over 30 years old.",
    difficulty: float = 0.5,
) -> str:
    """Generate valid multiple choice question JSON."""
    if alternatives is None:
        alternatives = ["1991", "1989", "1995", "2000"]
    if correct_answer is None:
        correct_answer = alternatives[0]

    return json.dumps({
        "statement": statement,
        "question_type": "multiple_choice",
        "alternatives": alternatives,
        "correct_answer": correct_answer,
        "explanation": explanation,
        "difficulty": difficulty,
    })


def valid_open_ended_question(
    statement: str = "Explain why Python is considered a beginner-friendly programming language.",
    rubric: str = "Key points: 1) Clear syntax 2) Readable code 3) Large community 4) Extensive documentation",
    explanation: str = "Python's design philosophy emphasizes code readability and simplicity, making it accessible for beginners.",
) -> str:
    """Generate valid open-ended question JSON."""
    return json.dumps({
        "statement": statement,
        "question_type": "open_ended",
        "alternatives": None,
        "correct_answer": rubric,
        "explanation": explanation,
        "difficulty": 0.4,
    })


def valid_fill_blank_question(
    statement: str = "Python was created by ___ and first released in 1991.",
    alternatives: list[str] | None = None,
    correct_answer: str = "Guido van Rossum",
) -> str:
    """Generate valid fill-in-the-blank question JSON."""
    if alternatives is None:
        alternatives = ["Guido van Rossum", "Linus Torvalds", "James Gosling", "Brendan Eich"]

    return json.dumps({
        "statement": statement,
        "question_type": "fill_in_the_blank",
        "alternatives": alternatives,
        "correct_answer": correct_answer,
        "explanation": "Guido van Rossum created Python and remained its principal author until 2018.",
        "difficulty": 0.3,
    })


def valid_supervision_result(approved: bool = True, feedback: str | None = None) -> str:
    """Generate valid supervision result JSON."""
    return json.dumps({
        "approved": approved,
        "feedback": feedback or ("Question meets quality standards." if approved else "Needs improvement."),
        "severity": None if approved else "minor",
    })


def valid_question_plan(specs: list[dict] | None = None) -> str:
    """Generate valid question plan JSON."""
    if specs is None:
        specs = [
            {"question_type": "multiple_choice", "focus_area": "Python history", "guidance": None},
            {"question_type": "multiple_choice", "focus_area": "Python features", "guidance": None},
            {"question_type": "open_ended", "focus_area": "Python applications", "guidance": None},
        ]

    return json.dumps({
        "total_questions": len(specs),
        "question_specs": specs,
    })


# =============================================================================
# Single Question Generation Tests
# =============================================================================

class TestSingleQuestionIntegration:
    """Integration tests for single question generation."""

    @pytest.mark.asyncio
    async def test_multiple_choice_from_content(self):
        """Test generating a multiple choice question from content."""
        mock_model = create_mock_model(valid_mc_question())

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=mock_model,
        )

        result = await generate_question(config)

        assert result.question is not None
        assert result.question.question_type == QuestionType.MULTIPLE_CHOICE
        assert result.question.statement == "What year was Python first released?"
        assert len(result.question.alternatives) == 4
        assert result.question.correct_answer in result.question.alternatives
        assert result.question.approved is True
        assert result.generation_time_ms > 0
        assert result.retries_used == 0

    @pytest.mark.asyncio
    async def test_open_ended_with_rubric(self):
        """Test generating an open-ended question with grading rubric."""
        mock_model = create_mock_model(valid_open_ended_question())

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.OPEN_ENDED,
            generator_model=mock_model,
        )

        result = await generate_question(config)

        assert result.question is not None
        assert result.question.question_type == QuestionType.OPEN_ENDED
        assert result.question.alternatives is None
        assert "Key points" in result.question.correct_answer  # Rubric
        assert len(result.question.explanation) >= 50

    @pytest.mark.asyncio
    async def test_fill_in_the_blank(self):
        """Test generating a fill-in-the-blank question."""
        mock_model = create_mock_model(valid_fill_blank_question())

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.FILL_IN_THE_BLANK,
            generator_model=mock_model,
        )

        result = await generate_question(config)

        assert result.question is not None
        assert result.question.question_type == QuestionType.FILL_IN_THE_BLANK
        assert "___" in result.question.statement
        assert result.question.correct_answer in result.question.alternatives

    @pytest.mark.asyncio
    async def test_topic_based_generation(self):
        """Test generating from a topic without content."""
        mock_model = create_mock_model(valid_mc_question(
            statement="What event marked the beginning of the French Revolution?",
            alternatives=["Storming of the Bastille", "Reign of Terror", "Tennis Court Oath", "Execution of Louis XVI"],
            correct_answer="Storming of the Bastille",
            explanation="The Storming of the Bastille on July 14, 1789 is widely considered the start of the French Revolution.",
        ))

        config = SingleQuestionConfig(
            topic="The French Revolution and its impact on European politics",
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=mock_model,
        )

        result = await generate_question(config)

        assert result.question is not None
        assert "French Revolution" in result.question.statement or "Bastille" in result.question.statement


# =============================================================================
# Multi-Language Support Tests
# =============================================================================

class TestMultiLanguageIntegration:
    """Integration tests for multi-language support."""

    @pytest.mark.asyncio
    async def test_portuguese_question_generation(self):
        """Test generating a question in Portuguese."""
        portuguese_question = json.dumps({
            "statement": "Em que ano Python foi lançado pela primeira vez?",
            "question_type": "multiple_choice",
            "alternatives": ["1991", "1989", "1995", "2000"],
            "correct_answer": "1991",
            "explanation": "Python foi criado por Guido van Rossum e lançado pela primeira vez em 1991.",
            "difficulty": 0.4,
        })

        mock_model = create_mock_model(portuguese_question)

        config = SingleQuestionConfig(
            content=PORTUGUESE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=mock_model,
            language="Portuguese",
        )

        result = await generate_question(config)

        assert result.question is not None
        # Verify Portuguese content
        assert "Python" in result.question.statement
        assert "1991" in result.question.explanation

    @pytest.mark.asyncio
    async def test_language_with_supervision(self):
        """Test that supervision works with language setting."""
        portuguese_question = json.dumps({
            "statement": "Qual é a principal característica do Python?",
            "question_type": "multiple_choice",
            "alternatives": ["Sintaxe clara", "Velocidade de execução", "Tipagem estática", "Compilação nativa"],
            "correct_answer": "Sintaxe clara",
            "explanation": "Python é conhecido principalmente por sua sintaxe clara e legível.",
            "difficulty": 0.3,
        })

        gen_model = create_mock_model(portuguese_question)
        sup_model = create_mock_model(valid_supervision_result(approved=True))

        config = SingleQuestionConfig(
            content=PORTUGUESE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=gen_model,
            supervisor_model=sup_model,
            supervision_enabled=True,
            language="Portuguese",
        )

        result = await generate_question(config)

        assert result.question is not None
        assert result.question.approved is True


# =============================================================================
# Supervision Tests
# =============================================================================

class TestSupervisionIntegration:
    """Integration tests for AI supervision."""

    @pytest.mark.asyncio
    async def test_supervision_approves_question(self):
        """Test that supervision can approve a question."""
        gen_model = create_mock_model(valid_mc_question())
        sup_model = create_mock_model(valid_supervision_result(approved=True))

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=gen_model,
            supervisor_model=sup_model,
            supervision_enabled=True,
            generator_instructions="Create challenging questions that test deep understanding.",
            supervisor_instructions="Ensure the question is unambiguous and all alternatives are plausible.",
        )

        result = await generate_question(config)

        assert result.question is not None
        assert result.question.approved is True
        assert result.retries_used == 0

    @pytest.mark.asyncio
    async def test_supervision_rejects_then_approves(self):
        """Test supervision rejection triggers retry and eventual approval."""
        # First generation, then rejection, then regeneration, then approval
        gen_responses = [
            valid_mc_question(statement="Vague question about Python that needs work?"),
            valid_mc_question(statement="What programming paradigms does Python support?"),
        ]
        sup_responses = [
            valid_supervision_result(approved=False, feedback="Question is too vague. Be more specific."),
            valid_supervision_result(approved=True),
        ]

        gen_model = create_sequential_mock_model(gen_responses)
        sup_model = create_sequential_mock_model(sup_responses)

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=gen_model,
            supervisor_model=sup_model,
            supervision_enabled=True,
            max_retries=3,
        )

        result = await generate_question(config)

        assert result.question is not None
        assert result.question.approved is True
        assert result.retries_used == 1  # One retry after rejection

    @pytest.mark.asyncio
    async def test_supervision_with_custom_instructions(self):
        """Test that custom instructions are passed to supervision."""
        gen_model = create_mock_model(valid_mc_question())
        sup_model = create_mock_model(valid_supervision_result(approved=True))

        config = SingleQuestionConfig(
            content="Medical terminology content about pharmacology...",
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=gen_model,
            supervisor_model=sup_model,
            supervision_enabled=True,
            generator_instructions="Focus on pharmacology terms and drug interactions.",
            supervisor_instructions="Verify medical accuracy and terminology precision.",
        )

        result = await generate_question(config)

        assert result.question is not None
        # Verify both models were called
        assert gen_model.ainvoke.called
        assert sup_model.ainvoke.called


# =============================================================================
# Multi-Question Generation Tests
# =============================================================================

class TestMultiQuestionIntegration:
    """Integration tests for multi-question generation."""

    @pytest.mark.asyncio
    async def test_multi_question_with_mix(self):
        """Test generating multiple questions with specific type mix."""
        responses = [
            valid_question_plan([
                {"question_type": "multiple_choice", "focus_area": "Python history", "guidance": None},
                {"question_type": "multiple_choice", "focus_area": "Python features", "guidance": None},
                {"question_type": "open_ended", "focus_area": "Python applications", "guidance": None},
            ]),
            valid_mc_question(statement="When was Python first released?"),
            valid_mc_question(statement="What paradigms does Python support?"),
            valid_open_ended_question(statement="Describe the main applications of Python in modern software development."),
        ]

        mock_model = create_sequential_mock_model(responses)

        config = MultiQuestionConfig(
            content=SAMPLE_CONTENT,
            num_questions=3,
            question_mix=[
                QuestionTypeMix(question_type=QuestionType.MULTIPLE_CHOICE, count=2),
                QuestionTypeMix(question_type=QuestionType.OPEN_ENDED, count=1),
            ],
            generator_model=mock_model,
        )

        result = await generate_questions(config)

        assert result.plan is not None
        assert result.plan.total_questions == 3
        assert len(result.questions) == 3
        assert result.generation_time_ms > 0

        # Verify mix
        mc_count = sum(1 for q in result.questions if q.question_type == QuestionType.MULTIPLE_CHOICE)
        oe_count = sum(1 for q in result.questions if q.question_type == QuestionType.OPEN_ENDED)
        assert mc_count == 2
        assert oe_count == 1

    @pytest.mark.asyncio
    async def test_multi_question_with_planning_instructions(self):
        """Test that planning instructions are used."""
        responses = [
            valid_question_plan([
                {"question_type": "multiple_choice", "focus_area": "Practical applications", "guidance": None},
                {"question_type": "multiple_choice", "focus_area": "Real-world usage", "guidance": None},
            ]),
            valid_mc_question(),
            valid_mc_question(),
        ]

        mock_model = create_sequential_mock_model(responses)

        config = MultiQuestionConfig(
            content=SAMPLE_CONTENT,
            num_questions=2,
            generator_model=mock_model,
            planning_instructions="Focus on practical applications and real-world usage only.",
        )

        result = await generate_questions(config)

        assert result.plan is not None
        assert len(result.questions) == 2

    @pytest.mark.asyncio
    async def test_multi_question_with_supervision(self):
        """Test multi-question generation with supervision enabled."""
        gen_responses = [
            valid_question_plan([
                {"question_type": "multiple_choice", "focus_area": "Topic 1", "guidance": None},
            ]),
            valid_mc_question(),
        ]
        sup_response = valid_supervision_result(approved=True)

        gen_model = create_sequential_mock_model(gen_responses)
        sup_model = create_mock_model(sup_response)

        config = MultiQuestionConfig(
            content=SAMPLE_CONTENT,
            num_questions=1,
            generator_model=gen_model,
            supervisor_model=sup_model,
            supervision_enabled=True,
        )

        result = await generate_questions(config)

        assert len(result.questions) == 1
        assert result.questions[0].approved is True


# =============================================================================
# Question Improvement Tests
# =============================================================================

class TestQuestionImprovementIntegration:
    """Integration tests for question improvement."""

    @pytest.mark.asyncio
    async def test_improve_question_basic(self):
        """Test basic question improvement flow."""
        original = Question(
            statement="What is Python? It is a programming language.",
            question_type=QuestionType.MULTIPLE_CHOICE,
            alternatives=["A snake", "A programming language", "A car", "A food"],
            correct_answer="A programming language",
            explanation="Python is a high-level programming language known for its clear syntax and readability.",
        )

        improved_json = json.dumps({
            "statement": "Which of the following best describes Python in the context of software development?",
            "question_type": "multiple_choice",
            "alternatives": [
                "A high-level programming language known for readability",
                "A compiled systems programming language",
                "A database query language",
                "A markup language for web pages",
            ],
            "correct_answer": "A high-level programming language known for readability",
            "explanation": "Python is a high-level, interpreted programming language designed with code readability in mind.",
            "difficulty": 0.4,
        })

        mock_model = create_mock_model(improved_json)

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=mock_model,
        )

        result = await improve_question(
            question=original,
            feedback="The distractors are too obvious. Make them more plausible and challenging.",
            config=config,
        )

        assert result.question is not None
        assert result.question.statement != original.statement
        assert result.generation_time_ms > 0
        assert result.retries_used == 0

    @pytest.mark.asyncio
    async def test_improve_question_with_language(self):
        """Test question improvement respects language setting."""
        original = Question(
            statement="What is Python and why is it popular?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            alternatives=["Language", "Snake", "Car", "Food"],
            correct_answer="Language",
            explanation="Python is a programming language created by Guido van Rossum in 1991.",
        )

        improved_json = json.dumps({
            "statement": "Qual é a principal característica que torna Python popular entre desenvolvedores?",
            "question_type": "multiple_choice",
            "alternatives": [
                "Sintaxe clara e legível",
                "Alta velocidade de execução",
                "Tipagem estática obrigatória",
                "Necessidade de compilação",
            ],
            "correct_answer": "Sintaxe clara e legível",
            "explanation": "Python é conhecida mundialmente por sua sintaxe clara e legível, facilitando o aprendizado.",
            "difficulty": 0.4,
        })

        mock_model = create_mock_model(improved_json)

        config = SingleQuestionConfig(
            content=PORTUGUESE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=mock_model,
            language="Portuguese",
        )

        result = await improve_question(
            question=original,
            feedback="Translate to Portuguese and make more specific.",
            config=config,
        )

        assert result.question is not None
        assert "Qual" in result.question.statement or "Python" in result.question.statement

    @pytest.mark.asyncio
    async def test_improve_open_ended_question(self):
        """Test improving an open-ended question with rubric."""
        original = Question(
            statement="Explain Python and its main features.",
            question_type=QuestionType.OPEN_ENDED,
            alternatives=None,
            correct_answer="Talk about Python features and why it is popular among developers.",
            explanation="Python is a programming language with many features and applications in various domains.",
        )

        improved_json = json.dumps({
            "statement": "Analyze and explain how Python's design philosophy of 'readability counts' influences its syntax and widespread adoption.",
            "question_type": "open_ended",
            "alternatives": None,
            "correct_answer": "Key points: 1) Explain Zen of Python 2) Give syntax examples 3) Compare to other languages 4) Discuss community impact",
            "explanation": "A complete answer should reference the Zen of Python, provide concrete syntax examples, and explain how this philosophy contributed to Python's adoption.",
            "difficulty": 0.6,
        })

        mock_model = create_mock_model(improved_json)

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.OPEN_ENDED,
            generator_model=mock_model,
        )

        result = await improve_question(
            question=original,
            feedback="Make the question more analytical and add a detailed grading rubric.",
            config=config,
        )

        assert result.question is not None
        assert result.question.question_type == QuestionType.OPEN_ENDED
        assert result.question.alternatives is None
        assert "Key points" in result.question.correct_answer


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    @pytest.mark.asyncio
    async def test_generation_error_after_max_retries(self):
        """Test that GenerationError is raised after max retries."""
        mock_model = AsyncMock()
        mock_model.ainvoke.side_effect = ValueError("Model failed to generate")

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=mock_model,
            max_retries=2,
        )

        with pytest.raises(GenerationError) as exc_info:
            await generate_question(config)

        assert "Model failed to generate" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_improve_question_error(self):
        """Test that improve_question raises GenerationError on failure."""
        original = Question(
            statement="What is Python? It is a programming language.",
            question_type=QuestionType.MULTIPLE_CHOICE,
            alternatives=["A", "B", "C", "D"],
            correct_answer="A",
            explanation="Python is a high-level programming language known for its clear syntax and readability.",
        )

        mock_model = AsyncMock()
        mock_model.ainvoke.side_effect = Exception("API error")

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=mock_model,
        )

        with pytest.raises(GenerationError) as exc_info:
            await improve_question(
                question=original,
                feedback="Improve this",
                config=config,
            )

        assert "Failed to improve question" in str(exc_info.value)
        assert exc_info.value.last_attempt == original

    @pytest.mark.asyncio
    async def test_validation_error_retry(self):
        """Test that validation errors trigger retries."""
        # First response is invalid JSON, second is valid
        responses = [
            "invalid json that will fail parsing",
            valid_mc_question(),
        ]

        mock_model = create_sequential_mock_model(responses)

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=mock_model,
            max_retries=3,
            retry_on_validation_error=True,
        )

        result = await generate_question(config)

        assert result.question is not None
        assert result.retries_used == 1


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestEdgeCasesIntegration:
    """Integration tests for edge cases."""

    @pytest.mark.asyncio
    async def test_question_with_minimum_difficulty(self):
        """Test question with difficulty at minimum (0.0)."""
        mock_model = create_mock_model(valid_mc_question(difficulty=0.0))

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=mock_model,
        )

        result = await generate_question(config)

        assert result.question.difficulty == 0.0

    @pytest.mark.asyncio
    async def test_question_with_maximum_difficulty(self):
        """Test question with difficulty at maximum (1.0)."""
        mock_model = create_mock_model(valid_mc_question(difficulty=1.0))

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=mock_model,
        )

        result = await generate_question(config)

        assert result.question.difficulty == 1.0

    @pytest.mark.asyncio
    async def test_all_question_types_in_single_multi_generation(self):
        """Test generating all three question types in one multi-generation."""
        responses = [
            valid_question_plan([
                {"question_type": "multiple_choice", "focus_area": "History", "guidance": None},
                {"question_type": "open_ended", "focus_area": "Analysis", "guidance": None},
                {"question_type": "fill_in_the_blank", "focus_area": "Facts", "guidance": None},
            ]),
            valid_mc_question(),
            valid_open_ended_question(),
            valid_fill_blank_question(),
        ]

        mock_model = create_sequential_mock_model(responses)

        config = MultiQuestionConfig(
            content=SAMPLE_CONTENT,
            num_questions=3,
            question_mix=[
                QuestionTypeMix(question_type=QuestionType.MULTIPLE_CHOICE, count=1),
                QuestionTypeMix(question_type=QuestionType.OPEN_ENDED, count=1),
                QuestionTypeMix(question_type=QuestionType.FILL_IN_THE_BLANK, count=1),
            ],
            generator_model=mock_model,
        )

        result = await generate_questions(config)

        assert len(result.questions) == 3
        types = {q.question_type for q in result.questions}
        assert QuestionType.MULTIPLE_CHOICE in types
        assert QuestionType.OPEN_ENDED in types
        assert QuestionType.FILL_IN_THE_BLANK in types

    @pytest.mark.asyncio
    async def test_supervision_multiple_rejections_then_approval(self):
        """Test multiple supervision rejections before approval."""
        gen_responses = [
            valid_mc_question(statement="Attempt 1"),
            valid_mc_question(statement="Attempt 2"),
            valid_mc_question(statement="Attempt 3 - finally good!"),
        ]
        sup_responses = [
            valid_supervision_result(approved=False, feedback="Too vague"),
            valid_supervision_result(approved=False, feedback="Still not specific enough"),
            valid_supervision_result(approved=True),
        ]

        gen_model = create_sequential_mock_model(gen_responses)
        sup_model = create_sequential_mock_model(sup_responses)

        config = SingleQuestionConfig(
            content=SAMPLE_CONTENT,
            question_type=QuestionType.MULTIPLE_CHOICE,
            generator_model=gen_model,
            supervisor_model=sup_model,
            supervision_enabled=True,
            max_retries=5,
        )

        result = await generate_question(config)

        assert result.question is not None
        assert result.question.approved is True
        assert result.retries_used >= 2  # At least two retries before success
