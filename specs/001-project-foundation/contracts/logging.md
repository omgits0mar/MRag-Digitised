# Contract: Structured Logging

**Module**: `mrag.logging`
**Consumers**: All modules

---

## Interface

### `get_logger(name: str) -> BoundLogger`

Returns a structured logger bound to the given module name.

**Parameters**:
- `name`: Module name, typically `__name__` (e.g., `"mrag.retrieval"`).

**Behavior**:
- Returns a `structlog.BoundLogger` with the `module` field pre-bound to `name`.
- Logger respects the `log_level` from `Settings` — entries below this level are not emitted.
- All output is JSON lines format: one JSON object per log entry to stdout.

### `configure_logging(log_level: str = "INFO") -> None`

Configures the global structlog pipeline. Called once at application startup.

**Parameters**:
- `log_level`: Minimum log level to emit. Default: `"INFO"`.

**Processor Pipeline** (in order):
1. `add_log_level` — adds `"level"` field
2. `TimeStamper(fmt="iso")` — adds `"timestamp"` field (ISO 8601)
3. `redact_sensitive_keys` — replaces values of sensitive keys with `"***"`
4. `JSONRenderer()` — serializes to JSON line

---

## Output Schema

Every log entry is a valid JSON object:

```json
{
  "timestamp": "2026-04-06T12:00:00.000000Z",
  "level": "info",
  "module": "mrag.config",
  "event": "Settings loaded",
  "num_fields": 20
}
```

**Required fields**: `timestamp`, `level`, `module`, `event`.
**Optional fields**: Any additional key-value pairs passed at log time.

---

## Redaction Contract

**Sensitive key patterns** (case-insensitive substring match):
`api_key`, `secret`, `password`, `token`, `credential`, `database_url`

Any log context field whose key matches a sensitive pattern has its value replaced with `"***"` before JSON serialization.

```python
logger.info("connecting", database_url="sqlite:///mrag.db")
# Output: {"database_url": "***", "event": "connecting", ...}
```

---

## Usage Example

```python
from mrag.logging import get_logger

logger = get_logger(__name__)
logger.info("Processing started", batch_size=100)
logger.warning("Slow query", latency_ms=1200, query_id="abc-123")
logger.error("Failed to connect", api_key="sk-xxx")  # api_key redacted to "***"
```
