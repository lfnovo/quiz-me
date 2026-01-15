# Configuration

## SingleQuestionConfig

For generating a single question.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `content` | `str` | * | - | Content to generate from |
| `topic` | `str` | * | - | Topic (uses model knowledge) |
| `question_type` | `QuestionType` | Yes | - | Type of question |
| `generator_model` | `Any` | Yes | - | LangChain-compatible model |
| `supervisor_model` | `Any` | No | `None` | Model for supervision |
| `supervision_enabled` | `bool` | No | `False` | Enable supervision |
| `language` | `str` | No | `None` | Target language for generation (e.g., "Portuguese") |
| `generator_instructions` | `str` | No | `None` | Custom instructions for generator |
| `supervisor_instructions` | `str` | No | `None` | Custom instructions for supervisor |
| `max_retries` | `int` | No | `3` | Max retry attempts |
| `retry_on_validation_error` | `bool` | No | `True` | Retry on Pydantic validation errors |

*Either `content` or `topic` must be provided (mutually exclusive).

### Language Support

The `language` property allows generating questions in any language:

```python
config = SingleQuestionConfig(
    content="Python é uma linguagem de programação...",
    question_type=QuestionType.MULTIPLE_CHOICE,
    generator_model=model,
    language="Portuguese",
)
```

When `language` is set:
- Question statement is generated in that language
- All alternatives are in that language
- Explanation is in that language
- Supervisor validates language correctness

---

## MultiQuestionConfig

For generating multiple questions with planning.

Inherits all fields from `SingleQuestionConfig` plus:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `num_questions` | `int` | Yes | - | Total questions to generate |
| `question_mix` | `list[QuestionTypeMix]` | No | `None` | Distribution of types |
| `planning_instructions` | `str` | No | `None` | Instructions for planner |

---

## QuestionTypeMix

Specify how many of each question type to generate.

```python
question_mix = [
    QuestionTypeMix(question_type=QuestionType.MULTIPLE_CHOICE, count=3),
    QuestionTypeMix(question_type=QuestionType.OPEN_ENDED, count=2),
]
# Total must equal num_questions
```

If `question_mix` is not provided, the planner decides the distribution.

---

## Question Improvement

Use `improve_question()` to regenerate a question based on feedback. This uses the same mechanism as supervision retry but allows post-hoc improvement.

```python
from quiz_me import improve_question, SingleQuestionConfig

# Original question that needs improvement
original = result.question

# Create config matching the original
config = SingleQuestionConfig(
    content="Original content...",
    question_type=original.question_type,
    generator_model=model,
    language="Portuguese",  # Optional: maintain language
)

# Improve based on feedback
improved = await improve_question(
    question=original,
    feedback="The distractors are too obvious. Make them more plausible.",
    config=config,
)
```

The `improve_question()` function:
- Takes the original question and user feedback
- Regenerates using the same prompt template with feedback context
- Returns a `GenerationResult` with the improved question
- Raises `GenerationError` if improvement fails
