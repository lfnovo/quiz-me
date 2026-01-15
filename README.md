# quiz-me

AI-powered question generation library using Langgraph flows. Generate high-quality educational questions from content or topics with optional AI supervision.

## Features

- **Single & Multi-Question Generation** - Generate one or multiple questions from content or topics
- **Three Question Types** - Multiple choice, open-ended (with grading rubric), and fill-in-the-blank
- **Optional AI Supervision** - A second model reviews and validates generated questions
- **Question Improvement** - Regenerate questions based on user feedback
- **Multi-Language Support** - Generate questions in any language
- **Automatic Retry Logic** - Retries on validation errors or supervision rejection
- **Domain-Specific Instructions** - Customize generation and supervision for your domain
- **LangChain Compatible** - Works with any LangChain-compatible model

## Installation

```bash
pip install quiz-me
```

Or with uv:
```bash
uv add quiz-me
```

## Quick Start

```python
from quiz_me import generate_question, SingleQuestionConfig, QuestionType

# Use any LangChain-compatible model
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4o-mini")

# Generate a multiple choice question
config = SingleQuestionConfig(
    content="Python is a high-level programming language...",
    question_type=QuestionType.MULTIPLE_CHOICE,
    generator_model=model,
)

result = await generate_question(config)
print(result.question.statement)
print(result.question.alternatives)
print(result.question.correct_answer)
```

## Topic-Based Generation

Generate questions from a topic using the model's knowledge (no content required):

```python
config = SingleQuestionConfig(
    topic="The French Revolution and its impact on European politics",
    question_type=QuestionType.MULTIPLE_CHOICE,
    generator_model=model,
)

result = await generate_question(config)
```

## Multi-Question Generation

```python
from quiz_me import generate_questions, MultiQuestionConfig, QuestionTypeMix

config = MultiQuestionConfig(
    content="Your educational content here...",
    num_questions=5,
    question_mix=[
        QuestionTypeMix(question_type=QuestionType.MULTIPLE_CHOICE, count=3),
        QuestionTypeMix(question_type=QuestionType.OPEN_ENDED, count=2),
    ],
    generator_model=model,
    planning_instructions="Focus on key concepts and practical applications",
)

result = await generate_questions(config)
for q in result.questions:
    print(q.statement)
```

## With Supervision

```python
config = SingleQuestionConfig(
    content="Medical terminology content...",
    question_type=QuestionType.MULTIPLE_CHOICE,
    generator_model=model,
    supervisor_model=model,  # Can be same or different model
    supervision_enabled=True,
    generator_instructions="Focus on pharmacology terms",
    supervisor_instructions="Verify medical accuracy",
)

result = await generate_question(config)
print(f"Approved: {result.question.approved}")
```

## Multi-Language Support

Generate questions in any language by setting the `language` property:

```python
config = SingleQuestionConfig(
    content="Python é uma linguagem de programação...",
    question_type=QuestionType.MULTIPLE_CHOICE,
    generator_model=model,
    language="Portuguese",  # All content generated in Portuguese
)

result = await generate_question(config)
# Question, alternatives, and explanation will be in Portuguese
```

## Question Improvement

Improve an existing question based on feedback using the same pattern as supervision:

```python
from quiz_me import improve_question

# Original question that needs improvement
original = result.question

# Create config matching the original question
config = SingleQuestionConfig(
    content="Original content...",
    question_type=original.question_type,
    generator_model=model,
)

# Improve based on feedback
improved = await improve_question(
    question=original,
    feedback="The distractors are too obvious. Make them more plausible.",
    config=config,
)
print(improved.question.statement)
```

## Retry Configuration

Control retry behavior for generation failures:

```python
config = SingleQuestionConfig(
    content="Your content...",
    question_type=QuestionType.MULTIPLE_CHOICE,
    generator_model=model,
    max_retries=5,                    # Default is 3
    retry_on_validation_error=True,   # Retry on Pydantic validation errors
)
```

## Documentation

See [docs/](docs/) for detailed documentation.

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest tests/ -v
```

## Stack

- **Langgraph** - Flow orchestration
- **Pydantic** - Data validation
- **ai-prompter** - Jinja-based prompt templates
- **LangChain** - Model abstraction

## License

MIT
