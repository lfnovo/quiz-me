# quiz-me Documentation

## API Reference

### Functions

| Function | Description |
|----------|-------------|
| `generate_question(config)` | Generate a single question |
| `generate_questions(config)` | Generate multiple questions with planning |
| `improve_question(question, feedback, config)` | Improve a question based on feedback |

### Configuration Classes

| Class | Use Case |
|-------|----------|
| `SingleQuestionConfig` | Single question generation |
| `MultiQuestionConfig` | Multi-question generation with planning |
| `QuestionTypeMix` | Specify distribution of question types |

### Models

| Model | Description |
|-------|-------------|
| `Question` | Generated question with all fields |
| `QuestionType` | Enum: `MULTIPLE_CHOICE`, `OPEN_ENDED`, `FILL_IN_THE_BLANK` |
| `QuestionSpec` | Specification for a single question in a plan |
| `QuestionPlan` | Plan for multi-question generation |
| `SupervisionResult` | Result from supervision review (approved, feedback, severity) |
| `GenerationResult` | Single question result with metadata |
| `MultiGenerationResult` | Multi-question result with plan |
| `GenerationError` | Exception for generation failures |

---

## Detailed Guides

- [Question Types](question-types.md)
- [Supervision](supervision.md)
- [Configuration](configuration.md)
- [Architecture](architecture.md)
