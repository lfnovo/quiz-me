# Question Types

## Multiple Choice

Questions with 3-5 alternatives where one is correct.

```python
config = SingleQuestionConfig(
    content="Your content...",
    question_type=QuestionType.MULTIPLE_CHOICE,
    generator_model=model,
)
```

**Output fields:**
- `statement` - The question text
- `alternatives` - List of 3-5 options
- `correct_answer` - The correct option (must be in alternatives)
- `explanation` - Why the answer is correct

---

## Open-Ended

Questions requiring free-form text responses.

```python
config = SingleQuestionConfig(
    content="Your content...",
    question_type=QuestionType.OPEN_ENDED,
    generator_model=model,
)
```

**Output fields:**
- `statement` - The question text
- `alternatives` - Always `None`
- `correct_answer` - **Grading rubric** with key points and criteria
- `explanation` - Model answer with educational context

---

## Fill-in-the-Blank

Statements with a blank (`___`) to complete.

```python
config = SingleQuestionConfig(
    content="Your content...",
    question_type=QuestionType.FILL_IN_THE_BLANK,
    generator_model=model,
)
```

**Output fields:**
- `statement` - Text with `___` for the blank
- `alternatives` - List of 3-5 options to fill the blank
- `correct_answer` - The correct option
- `explanation` - Why this answer is correct

---

## Common Fields (All Types)

All question types include these additional fields:

| Field | Type | Description |
|-------|------|-------------|
| `difficulty` | `float \| None` | Difficulty rating from 0.0 (easy) to 1.0 (hard) |
| `approved` | `bool` | Supervision approval status (default: `True`) |
| `supervision_feedback` | `str \| None` | Feedback from supervisor if rejected |
