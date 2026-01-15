# Supervision

Supervision enables a second AI model to review generated questions for quality.

## Enabling Supervision

```python
config = SingleQuestionConfig(
    content="Your content...",
    question_type=QuestionType.MULTIPLE_CHOICE,
    generator_model=generator_model,
    supervisor_model=supervisor_model,  # Required when enabled
    supervision_enabled=True,
)
```

## How It Works

1. Generator creates a question
2. Supervisor reviews and approves/rejects
3. If rejected and retries available, generator tries again with feedback
4. Process repeats until approved or max retries reached

## Custom Instructions

```python
config = SingleQuestionConfig(
    # ...
    generator_instructions="Focus on advanced concepts only",
    supervisor_instructions="Reject questions that are too easy",
    max_retries=5,  # Default is 3
)
```

## Supervision Result

The `Question` model includes supervision status:

```python
result = await generate_question(config)
print(result.question.approved)  # True/False
print(result.question.supervision_feedback)  # Feedback if rejected
print(result.retries_used)  # Number of regeneration attempts
```

## Using Different Models

You can use a stronger model for supervision:

```python
generator = ChatOpenAI(model="gpt-4o-mini")  # Faster, cheaper
supervisor = ChatOpenAI(model="gpt-4o")      # More thorough

config = SingleQuestionConfig(
    # ...
    generator_model=generator,
    supervisor_model=supervisor,
    supervision_enabled=True,
)
```
