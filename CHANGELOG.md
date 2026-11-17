# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-17

### Changed

- **Breaking:** minimum supported Python is now 3.11 (Python 3.10 reached end of life in October 2026).
- Raised minimum dependency versions: `langchain-core>=1.0.0`, `ai-prompter>=0.4.0`.
- Raised minimum dev dependency versions: `pytest>=9.0`, `pytest-asyncio>=1.0`.
- Refreshed the lockfile to the latest compatible releases (langgraph 1.2, langchain-core 1.8, pydantic 2.14, ai-prompter 0.4).
- CI test matrix now runs on Python 3.11 and 3.12.
