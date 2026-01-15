# Architecture

## Overview

quiz-me uses Langgraph for flow orchestration with Pydantic state management.

```
┌─────────────────────────────────────────────────────────┐
│                      Public API                         │
│  generate_question()          generate_questions()      │
└────────────────┬────────────────────────┬───────────────┘
                 │                        │
    ┌────────────▼────────────┐  ┌────────▼────────────┐
    │  Single Question Flow   │  │  Multi Question Flow │
    │  (single.py)            │  │  (multi.py)          │
    └────────────┬────────────┘  └────────┬────────────┘
                 │                        │
    ┌────────────▼────────────────────────▼───────────────┐
    │                      Nodes                          │
    │  generate, supervise, plan, finalize                │
    └────────────┬────────────────────────────────────────┘
                 │
    ┌────────────▼────────────────────────────────────────┐
    │               Prompt Templates                      │
    │  generate_question.jinja, supervise_question.jinja  │
    └─────────────────────────────────────────────────────┘
```

## Single Question Flow

```
START → generate → should_supervise_or_retry?
    ├─→ (error, can retry) → generate
    ├─→ (no supervision) → END
    └─→ (supervision) → supervise → should_retry?
        ├─→ (approved) → END
        ├─→ (rejected, can retry) → generate
        └─→ (rejected, max retries) → END
```

## Multi Question Flow

```
START → plan → generate → should_supervise?
    ├─→ (no supervision) → finalize → should_continue?
    └─→ (supervision) → supervise → should_retry?
        ├─→ (retry) → generate
        └─→ (done) → finalize → should_continue?
            ├─→ (more questions) → generate
            └─→ (all done) → END
```

## Key Components

| Component | Location | Description |
|-----------|----------|-------------|
| Config | `config.py` | Configuration classes |
| Models | `models.py` | Pydantic data models |
| States | `states.py` | Langgraph state schemas |
| Nodes | `nodes/` | Flow node implementations |
| Flows | `flows/` | Langgraph flow definitions |
| Prompts | `prompts/` | Jinja templates |
