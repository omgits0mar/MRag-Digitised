"""LLM client abstraction + Groq-compatible implementation.

Defines a ``BaseLLMClient`` ABC so providers can be swapped without
touching the generation pipeline (Constitution Article V). The default
``GroqLLMClient`` targets any OpenAI-compatible ``/chat/completions``
endpoint and implements exponential-backoff retry over httpx async.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

import httpx
import structlog

from mrag.exceptions import ResponseGenerationError

logger = structlog.get_logger(__name__)


class BaseLLMClient(ABC):
    """Abstract interface for LLM providers.

    Implementations must be awaitable and raise ``ResponseGenerationError``
    on any non-recoverable failure after retries.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a completion for the given prompt.

        Args:
            prompt: User/assistant prompt content.
            system_prompt: Optional system instruction.
            temperature: Sampling temperature in ``[0.0, 2.0]``.
            max_tokens: Max tokens in the generated response.

        Returns:
            Generated text (never None / never empty unless the provider
            explicitly returned an empty completion).

        Raises:
            ResponseGenerationError: On API failure after all retries.
        """


class GroqLLMClient(BaseLLMClient):
    """Groq / OpenAI-compatible ``/chat/completions`` client.

    Args:
        api_url: Base URL including ``/v1`` path, e.g. ``https://api.groq.com/openai/v1``.
        api_key: Bearer token used in the ``Authorization`` header.
        model_name: Model identifier (default ``llama3-8b-8192``).
        timeout: Per-request timeout in seconds.
        max_retries: Maximum retry attempts on transient failures.
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        model_name: str = "llama3-8b-8192",
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name
        self._timeout = timeout
        self._max_retries = max_retries

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> str:
        """POST a chat completion request with exponential-backoff retry."""
        url = f"{self._api_url}/chat/completions"
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)

                # Retry on transient errors, fail fast on client errors.
                if response.status_code == 429 or response.status_code >= 500:
                    logger.warning(
                        "llm_transient_error",
                        status=response.status_code,
                        attempt=attempt + 1,
                    )
                    last_exc = ResponseGenerationError(
                        f"LLM transient error: HTTP {response.status_code}",
                        detail={"status": response.status_code},
                    )
                    await asyncio.sleep(min(2**attempt, 10))
                    continue

                if response.status_code >= 400:
                    raise ResponseGenerationError(
                        f"LLM client error: HTTP {response.status_code}",
                        detail={"status": response.status_code, "body": response.text},
                    )

                data = response.json()
                try:
                    content = data["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise ResponseGenerationError(
                        "Malformed LLM response payload",
                        detail={"payload": data},
                    ) from exc

                logger.info(
                    "llm_generate_success",
                    model=self._model_name,
                    response_length=len(content or ""),
                    attempt=attempt + 1,
                )
                return content or ""

            except httpx.TimeoutException as exc:
                last_exc = exc
                logger.warning(
                    "llm_timeout",
                    attempt=attempt + 1,
                    timeout=self._timeout,
                )
                await asyncio.sleep(min(2**attempt, 10))
            except httpx.HTTPError as exc:
                last_exc = exc
                logger.warning(
                    "llm_http_error",
                    attempt=attempt + 1,
                    error=str(exc),
                )
                await asyncio.sleep(min(2**attempt, 10))
            except ResponseGenerationError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.error(
                    "llm_unexpected_error",
                    attempt=attempt + 1,
                    error=str(exc),
                )
                await asyncio.sleep(min(2**attempt, 10))

        raise ResponseGenerationError(
            f"LLM call failed after {self._max_retries} attempts",
            detail={"last_error": str(last_exc) if last_exc else "unknown"},
        )
