# Research: Project Foundation & Environment Setup

**Branch**: `001-project-foundation` | **Date**: 2026-04-06
**Spec**: `specs/001-project-foundation/spec.md`

---

## R-001: Configuration Management — Pydantic BaseSettings

**Decision**: Use `pydantic-settings` (v2) with `BaseSettings` for typed, validated configuration.

**Rationale**:
- Pydantic v2 `BaseSettings` collects ALL validation errors by default — `ValidationError` contains a list of every invalid/missing field, satisfying FR-003 (aggregate error reporting).
- `SettingsConfigDict(frozen=True)` makes the settings instance immutable after creation, satisfying the clarified FR-002 (load-once, read-many).
- `SecretStr` type masks sensitive values in `repr()` and `str()`, providing a foundation for FR-005a (log redaction).
- Environment variables take precedence over `.env` file values by default, satisfying FR-002 precedence rules.
- `pydantic-settings` is a separate package from `pydantic` in v2 — both must be pinned.

**Alternatives Considered**:
- `python-decouple`: Simpler but no type validation, no aggregate error reporting, no immutability.
- `dynaconf`: Feature-rich but heavyweight for this use case, adds unnecessary complexity.
- `python-dotenv` + `dataclasses`: Manual type validation needed, no built-in aggregate error collection.
- Plain `os.environ`: No validation, no type coercion, no structure. Rejected per Article IX.

---

## R-002: Structured Logging — structlog

**Decision**: Use `structlog` (v24.x) with `JSONRenderer` for JSON lines output.

**Rationale**:
- `structlog.processors.JSONRenderer()` produces one JSON object per log line, satisfying FR-004.
- Custom processors can intercept and redact sensitive fields before serialization, satisfying FR-005a. Pattern: define a `redact_sensitive_keys` processor that checks field names against a configurable set of sensitive key patterns (e.g., `api_key`, `secret`, `password`, `token`) and replaces values with `"***"`.
- `structlog` integrates cleanly with Python's `logging` stdlib — it can wrap stdlib loggers or operate standalone. For this project, configure structlog as the primary logger with stdlib integration so third-party libraries using `logging` also produce structured output.
- `structlog.get_logger()` returns a bound logger with lazy binding — modules call `get_logger(__name__)` for per-module identification.
- Processors chain: `add_log_level` → `TimeStamper(fmt="iso")` → `redact_sensitive_keys` → `JSONRenderer()`.

**Alternatives Considered**:
- `python-json-logger`: Limited to stdlib `logging`, no processor pipeline, no built-in redaction support.
- `loguru`: Feature-rich but opinionated, harder to integrate with stdlib, no processor chain.
- stdlib `logging` with JSON formatter: Possible but requires significant custom code for structured context binding and redaction.

---

## R-003: Python Package Structure — src/ Layout

**Decision**: Use `src/mrag/` layout with `pyproject.toml` and `setuptools` as build backend.

**Rationale**:
- `src/` layout prevents accidental imports of the local package during development — the package must be installed to be importable, catching packaging errors early.
- `setuptools` with `pyproject.toml` is the most mature and widely-supported build backend for editable installs (`pip install -e .`). Hatchling and flit are viable but setuptools has the broadest compatibility with CI/CD tooling.
- `requires-python = ">=3.10"` in `[project]` enforces FR-009 at install time — pip will refuse to install on older Python.
- Dev dependencies separated via `[project.optional-dependencies]` under a `dev` key: `pip install -e ".[dev]"` installs everything; `pip install -e .` installs only runtime deps.
- Version defined as a string in `src/mrag/__init__.py` (`__version__ = "0.1.0"`) and referenced dynamically from pyproject.toml using `[tool.setuptools.dynamic]` — single source of truth.

**Alternatives Considered**:
- `hatchling`: Clean but less mature editable install support in some CI environments.
- `flit`: Minimal but doesn't support complex build customization if needed later.
- `poetry`: Adds a separate lock file format and CLI tool; heavier than needed. pyproject.toml with setuptools is sufficient.
- Flat layout (no `src/`): Risk of import shadowing during development. Rejected per spec assumption.

---

## R-004: Code Quality Tooling — black + ruff

**Decision**: Use `black` for formatting, `ruff` for linting (replacing flake8 + isort).

**Rationale**:
- `ruff` is a drop-in replacement for `flake8`, `isort`, `pyflakes`, `pycodestyle`, and many more — single tool, vastly faster (written in Rust).
- Configure ruff in `[tool.ruff]` section of `pyproject.toml` — no separate config files needed.
- `ruff` respects black's formatting by default when `line-length` matches. Set both to `line-length = 88` (black's default).
- Enable rule sets: `E` (pycodestyle errors), `F` (pyflakes), `I` (isort), `UP` (pyupgrade), `B` (flake8-bugbear), `SIM` (flake8-simplify).
- Target version: `target-version = "py310"` to match the project's minimum Python version.

**Alternatives Considered**:
- `flake8` + `isort` separately: Works but slower, requires two tools and two configs. ruff subsumes both.
- `ruff format` (replacing black): Possible in newer ruff versions, but black is explicitly mandated by the constitution (Article IX). Use both: black formats, ruff lints.

---

## R-005: Exception Hierarchy Design

**Decision**: Single-inheritance tree rooted at `MRAGError(Exception)` with one subclass per module.

**Rationale**:
- Base `MRAGError` inherits from `Exception` (not `BaseException`) — follows Python best practice for application exceptions.
- Each module gets one exception class (e.g., `DataProcessingError`, `EmbeddingError`, `RetrievalError`) that inherits from `MRAGError`.
- Module-specific sub-exceptions (e.g., `ChunkingError(DataProcessingError)`) are deferred to each module's feature implementation — the foundation only provides the first two levels.
- All exceptions accept `message: str` and optional `detail: dict[str, Any]` for structured error context — aligns with the API error schema (`{"error": str, "detail": str, "status_code": int}`).
- `__str__` and `__repr__` use the message field for consistency.

**Alternatives Considered**:
- Flat exceptions (no hierarchy): Prevents catching all project exceptions uniformly. Rejected.
- Mixin-based exceptions: Adds complexity for no benefit at this stage.
- `attrs`-based exceptions: Overkill for simple exception classes.

---

## R-006: Testing Framework

**Decision**: `pytest` with `pytest-asyncio` and `pytest-cov` for coverage reporting.

**Rationale**:
- `pytest` is the de facto Python testing standard, with rich plugin ecosystem.
- `pytest-asyncio` needed for async test support in later phases (FastAPI, async DB operations).
- `pytest-cov` for code coverage measurement — useful for CI reporting.
- Test layout: `tests/unit/`, `tests/integration/`, `tests/evaluation/` mirroring the project phases.
- `conftest.py` at root provides shared fixtures: temp config, temp directories, sample data factories.

**Alternatives Considered**:
- `unittest`: Built-in but verbose, less ergonomic, weaker fixture model.
- `nose2`: Maintenance mode, pytest is the community standard.
