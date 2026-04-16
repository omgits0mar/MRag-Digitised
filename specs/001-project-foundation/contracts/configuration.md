# Contract: Configuration Access

**Module**: `mrag.config`
**Consumers**: All modules

---

## Interface

### `get_settings() -> Settings`

Returns the singleton, immutable `Settings` instance. Loads configuration on first call; subsequent calls return the cached instance.

**Behavior**:
- First invocation: reads `.env` file (if present) and environment variables, validates all fields, returns frozen `Settings` instance.
- Subsequent invocations: returns the same instance (no re-loading).
- If `.env` file is missing: logs a warning, proceeds with environment variables and defaults only.
- If validation fails: raises `ValidationError` containing ALL invalid/missing fields (aggregate), not just the first.

**Precedence** (highest to lowest):
1. Environment variables
2. `.env` file values
3. Field defaults in `Settings` class

### `Settings` (frozen Pydantic model)

- All fields have type annotations.
- All fields with defaults can be omitted from `.env`.
- Fields marked `SecretStr` never expose their value in `repr()` or `str()`.
- Instance is frozen — attribute assignment raises `ValidationError`.

---

## Error Contract

| Condition | Exception | Detail |
|---|---|---|
| One or more invalid/missing fields | `pydantic.ValidationError` | List of all errors with field name, expected type, and message |
| Attribute mutation attempted | `pydantic.ValidationError` | "Instance is frozen" |

---

## Usage Example

```python
from mrag.config import get_settings

settings = get_settings()
print(settings.top_k)           # 5
print(settings.llm_api_key)     # SecretStr('**********')
settings.top_k = 10             # Raises ValidationError (frozen)
```
