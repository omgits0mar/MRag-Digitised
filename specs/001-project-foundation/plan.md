# Implementation Plan: Project Foundation & Environment Setup

**Branch**: `001-project-foundation` | **Date**: 2026-04-06 | **Spec**: `specs/001-project-foundation/spec.md`
**Input**: Feature specification from `specs/001-project-foundation/spec.md`
**Constitution Version**: 1.0.0

## Summary

Establish the complete Python project scaffold for the Multilingual RAG Platform (MRAG): `src/mrag/` package with 9 importable sub-modules, a Pydantic-based immutable configuration system with aggregate validation, structlog-based JSON logging with sensitive field redaction, a shared exception hierarchy, and a dev toolchain (black + ruff + pytest) accessible via Makefile targets. This is the Phase 0 prerequisite for all subsequent features.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: pydantic (v2), pydantic-settings, structlog, black, ruff, pytest, pytest-asyncio, pytest-cov, python-dotenv
**Storage**: N/A (foundation only; SQLite/MySQL deferred to Feature 008)
**Testing**: pytest + pytest-asyncio + pytest-cov
**Target Platform**: Linux server / macOS (dev)
**Project Type**: Library + Web Service (foundation scaffolding)
**Performance Goals**: N/A for foundation (developer setup < 5 minutes per SC-001)
**Constraints**: Offline-capable after initial `pip install`, Unix-like OS only, Python >= 3.10 enforced at install time
**Scale/Scope**: 9 module sub-packages, ~20 config fields, foundation for ~300K Q&A pair RAG system

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Applies | Status | Evidence |
|---|---|---|---|
| I — Modular Architecture | Yes | **PASS** | 9 independent sub-packages with `__init__.py`, clear module boundaries |
| II — Data Integrity | No | — | Foundation only, no data processing |
| III — Multilingual-First | No | — | Foundation only; UTF-8 encoding default noted |
| IV — Retrieval Quality | No | — | No retrieval in this feature |
| V — LLM Contract | No | — | No LLM integration; placeholder config fields prepared |
| VI — Testing | Yes | **PASS** | pytest setup, unit tests for config/logging, test directory structure |
| VII — API Design | No | — | API module created as empty placeholder |
| VIII — Performance/Caching | No | — | Foundation only; cache config fields prepared |
| IX — Code Quality | Yes | **PASS** | black + ruff (zero violations), type hints mandatory, structlog (no prints), pinned deps, secrets in `.env` |
| X — Doc Separation | Yes | **PASS** | Spec is technology-agnostic, plan contains all tech decisions |

**Gate Result: PASSED** — No violations. No complexity justification needed.

## Tech Stack Decisions

| Component | Choice | Rationale | Research Ref |
|---|---|---|---|
| Package layout | `src/mrag/` with setuptools | Prevents import shadowing, mature editable install support | R-003 |
| Build system | `pyproject.toml` + setuptools | Standard, broadest CI compatibility, `pip install -e .` works | R-003 |
| Config | Pydantic `BaseSettings` (v2) | Typed validation, aggregate errors, `.env` support, `frozen=True`, `SecretStr` | R-001 |
| Logging | `structlog` with `JSONRenderer` | JSON lines output, processor pipeline for redaction | R-002 |
| Formatting | `black` (line-length=88) | Constitution Article IX mandate | R-004 |
| Linting | `ruff` (replaces flake8+isort) | Single tool, Rust-speed, configured in pyproject.toml | R-004 |
| Testing | `pytest` + `pytest-asyncio` + `pytest-cov` | De facto standard, async support for later phases | R-006 |
| Task runner | `Makefile` | Simple, portable, zero extra dependencies | Master plan |
| Exceptions | Single-inheritance tree from `MRAGError` | Uniform catching, structured detail field | R-005 |

## Project Structure

### Documentation (this feature)

```text
specs/001-project-foundation/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 entity definitions
├── quickstart.md        # Developer onboarding guide
├── checklists/
│   └── requirements.md  # Requirements checklist
└── contracts/
    ├── configuration.md # Config access contract
    ├── logging.md       # Logging contract
    └── exceptions.md    # Exception hierarchy contract
```

### Source Code (repository root)

```text
pyproject.toml               # Build config, dependencies, tool settings
Makefile                     # install, test, lint, format, clean targets
.env.example                 # Documented config template
.gitignore                   # Python, venvs, .env, FAISS, __pycache__
src/
└── mrag/
    ├── __init__.py          # __version__, package metadata
    ├── config.py            # Settings(BaseSettings) — frozen, aggregate validation
    ├── logging.py           # configure_logging(), get_logger(), redaction processor
    ├── exceptions.py        # MRAGError + 9 module exception subclasses
    ├── data/
    │   └── __init__.py      # Placeholder (Feature 001)
    ├── embeddings/
    │   └── __init__.py      # Placeholder (Feature 002)
    ├── retrieval/
    │   └── __init__.py      # Placeholder (Feature 003)
    ├── query/
    │   └── __init__.py      # Placeholder (Feature 004)
    ├── generation/
    │   └── __init__.py      # Placeholder (Feature 005)
    ├── cache/
    │   └── __init__.py      # Placeholder (Feature 006)
    ├── api/
    │   └── __init__.py      # Placeholder (Feature 007)
    ├── db/
    │   └── __init__.py      # Placeholder (Feature 008)
    └── evaluation/
        └── __init__.py      # Placeholder (Feature 009)
tests/
├── conftest.py              # Shared fixtures: temp config, env overrides
├── unit/
│   ├── test_config.py       # Settings loading, validation, immutability, precedence
│   ├── test_logging.py      # JSON output, redaction, log levels
│   └── test_exceptions.py   # Hierarchy, inheritance, detail field
├── integration/             # Empty (future phases)
└── evaluation/              # Empty (future phases)
data/
├── raw/                     # Raw dataset files
├── processed/               # Processed/chunked data
└── evaluation/              # Evaluation datasets
prompts/
└── templates/               # Externalized prompt templates
```

**Structure Decision**: Single-project `src/` layout selected per R-003 research. No monorepo or multi-package structure needed — all 9 modules are sub-packages of a single `mrag` package. This matches the constitution's modular architecture (Article I) while keeping packaging simple.

## Key Design Decisions

### D-001: Configuration Immutability (from Clarification)

Configuration is frozen after initialization. Modules receive the same `Settings` instance throughout the application lifetime. This eliminates race conditions and allows modules to safely cache config values locally.

### D-002: Aggregate Validation (from Clarification)

Pydantic v2 `BaseSettings` natively collects all validation errors into a single `ValidationError`. No custom aggregation code needed — this is the default behavior. The error message lists every invalid/missing field with its expected type.

### D-003: JSON Lines Log Format (from Clarification)

All log output uses `structlog.processors.JSONRenderer()` producing one valid JSON object per line. This is directly testable: parse each line with `json.loads()` and assert required fields exist.

### D-004: Sensitive Field Redaction (from Clarification)

A custom structlog processor (`redact_sensitive_keys`) runs before `JSONRenderer` in the processor chain. It performs case-insensitive substring matching on log context keys against a configurable set of patterns: `api_key`, `secret`, `password`, `token`, `credential`, `database_url`. Matching values are replaced with `"***"`.

### D-005: Version Management

`__version__` is defined in `src/mrag/__init__.py` as a string literal. `pyproject.toml` reads it dynamically via `[tool.setuptools.dynamic] version = {attr = "mrag.__version__"}`. Single source of truth.

### D-006: Dependency Pinning Strategy

All runtime and dev dependencies are pinned to exact versions in `pyproject.toml` under `[project.dependencies]` and `[project.optional-dependencies.dev]` respectively. This satisfies FR-010 and Article IX. Example: `pydantic==2.10.6`, not `pydantic>=2.10`.

## Post-Design Constitution Re-Check

| Article | Status | Notes |
|---|---|---|
| I | **PASS** | 9 sub-packages with clear boundaries, explicit I/O contracts in `contracts/` |
| VI | **PASS** | Test structure defined, unit tests cover config/logging/exceptions |
| IX | **PASS** | black+ruff in pyproject.toml, type hints required, structlog JSON, pinned deps, SecretStr for secrets |
| X | **PASS** | Spec contains no tech details, all tech decisions in this plan |

**Post-Design Gate: PASSED**

## Complexity Tracking

No violations to justify. All design choices are the simplest approach that satisfies the requirements.

## References

- [Research](research.md) — Technology decisions and alternatives
- [Data Model](data-model.md) — Entity definitions (Settings, Logger, Exception Hierarchy)
- [Contracts](contracts/) — Interface contracts for config, logging, exceptions
- [Quickstart](quickstart.md) — Developer onboarding guide
- [Spec](spec.md) — Feature specification with clarifications
- [Constitution](../../.specify/memory/constitution.md) — Project principles (v1.0.0)
- [Master Plan](../../mrag-project-plan.md) — Project-wide feature dependency map
