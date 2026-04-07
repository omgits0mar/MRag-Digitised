# Quickstart: Project Foundation

**Branch**: `001-project-foundation` | **Date**: 2026-04-06

---

## Prerequisites

- Python 3.10 or higher
- Git
- Unix-like OS (Linux or macOS)

## Setup (< 5 minutes)

### 1. Clone and enter the repository

```bash
git clone <repository-url>
cd mrag
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
make install
```

This runs `pip install -e ".[dev]"`, installing both runtime and development dependencies.

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your values (at minimum, set LLM_API_KEY)
```

### 5. Verify setup

```bash
make test    # Run test suite
make lint    # Check code quality
make format  # Auto-format code
```

All three commands should pass with zero errors.

## Available Commands

| Command | Description |
|---|---|
| `make install` | Install package with all dependencies (editable mode) |
| `make test` | Run pytest test suite |
| `make lint` | Run ruff linter (zero violations required) |
| `make format` | Run black + ruff auto-formatting |
| `make clean` | Remove caches, compiled files, build artifacts |

## Configuration

All settings are managed through environment variables or a `.env` file. See `.env.example` for the full list with descriptions.

**Precedence**: Environment variable > `.env` file > default value.

**Validation**: On startup, all values are validated. If any value is invalid or a required value is missing, a single error listing ALL issues is raised.

**Immutability**: Configuration is loaded once at startup and cannot be changed at runtime. Restart the application to apply changes.

## Project Structure

```
src/mrag/
├── __init__.py          # Package root, exposes __version__
├── config.py            # Centralized configuration (Settings)
├── logging.py           # Structured JSON logging
├── exceptions.py        # Shared exception hierarchy
├── data/                # Data processing (Feature 001)
├── embeddings/          # Embedding generation (Feature 002)
├── retrieval/           # Vector search (Feature 003)
├── query/               # Query processing (Feature 004)
├── generation/          # Response generation (Feature 005)
├── cache/               # Caching & performance (Feature 006)
├── api/                 # FastAPI endpoints (Feature 007)
├── db/                  # Database integration (Feature 008)
└── evaluation/          # Evaluation framework (Feature 009)
```

## Logging

All modules use structured JSON logging:

```python
from mrag.logging import get_logger

logger = get_logger(__name__)
logger.info("Operation completed", items_processed=42)
```

Output (JSON lines):
```json
{"timestamp": "2026-04-06T12:00:00Z", "level": "info", "module": "mrag.data", "event": "Operation completed", "items_processed": 42}
```

Sensitive fields (API keys, passwords) are automatically redacted in log output.
