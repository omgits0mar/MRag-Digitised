"""Unit tests for mrag.generation.llm_client (BaseLLMClient + GroqLLMClient)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from mrag.exceptions import ResponseGenerationError
from mrag.generation.llm_client import BaseLLMClient, GroqLLMClient


def _mk_httpx_response(status: int, body: dict | None = None) -> httpx.Response:
    body = body if body is not None else {}
    return httpx.Response(status_code=status, text=json.dumps(body))


class TestBaseLLMClientContract:
    def test_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            BaseLLMClient()  # type: ignore[abstract]

    def test_subclass_must_implement_generate(self) -> None:
        class Partial(BaseLLMClient):
            pass

        with pytest.raises(TypeError):
            Partial()  # type: ignore[abstract]


@pytest.mark.asyncio
class TestGroqLLMClient:
    @pytest.fixture()
    def ok_payload(self) -> dict:
        return {
            "choices": [{"message": {"role": "assistant", "content": "hello world"}}]
        }

    async def test_generate_success(self, ok_payload: dict) -> None:
        client = GroqLLMClient(
            api_url="https://api.example.com/v1",
            api_key="sk-test",
            model_name="llama3-test",
            timeout=5,
            max_retries=2,
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=_mk_httpx_response(200, ok_payload))
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = False

        with patch(
            "mrag.generation.llm_client.httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await client.generate("test prompt", system_prompt="sys")

        assert result == "hello world"
        mock_client.post.assert_awaited_once()
        # Verify headers and body.
        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["headers"]["Authorization"] == "Bearer sk-test"
        assert call_kwargs["json"]["model"] == "llama3-test"
        assert call_kwargs["json"]["messages"][0]["role"] == "system"
        assert call_kwargs["json"]["messages"][1]["role"] == "user"

    async def test_retry_on_429_then_success(self, ok_payload: dict) -> None:
        client = GroqLLMClient(
            api_url="https://api.example.com/v1",
            api_key="sk-test",
            max_retries=3,
            timeout=1,
        )

        post_mock = AsyncMock(
            side_effect=[
                _mk_httpx_response(429, {}),
                _mk_httpx_response(200, ok_payload),
            ]
        )
        mock_client = AsyncMock()
        mock_client.post = post_mock
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = False

        with (
            patch(
                "mrag.generation.llm_client.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch("mrag.generation.llm_client.asyncio.sleep", new=AsyncMock()),
        ):
            result = await client.generate("p")
        assert result == "hello world"
        assert post_mock.await_count == 2

    async def test_retry_on_500_eventually_fails(self) -> None:
        client = GroqLLMClient(
            api_url="https://api.example.com/v1",
            api_key="sk-test",
            max_retries=2,
            timeout=1,
        )
        post_mock = AsyncMock(return_value=_mk_httpx_response(500, {}))
        mock_client = AsyncMock()
        mock_client.post = post_mock
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = False

        with (
            patch(
                "mrag.generation.llm_client.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch("mrag.generation.llm_client.asyncio.sleep", new=AsyncMock()),
            pytest.raises(ResponseGenerationError),
        ):
            await client.generate("p")
        assert post_mock.await_count == 2

    async def test_400_fails_fast(self) -> None:
        client = GroqLLMClient(
            api_url="https://api.example.com/v1",
            api_key="sk-test",
            max_retries=3,
            timeout=1,
        )
        post_mock = AsyncMock(return_value=_mk_httpx_response(400, {}))
        mock_client = AsyncMock()
        mock_client.post = post_mock
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = False

        with patch(
            "mrag.generation.llm_client.httpx.AsyncClient",
            return_value=mock_client,
        ), pytest.raises(ResponseGenerationError):
            await client.generate("p")
        # 4xx errors do not retry.
        assert post_mock.await_count == 1

    async def test_timeout_retried(self, ok_payload: dict) -> None:
        client = GroqLLMClient(
            api_url="https://api.example.com/v1",
            api_key="sk-test",
            max_retries=2,
            timeout=1,
        )
        post_mock = AsyncMock(
            side_effect=[
                httpx.TimeoutException("timeout"),
                _mk_httpx_response(200, ok_payload),
            ]
        )
        mock_client = AsyncMock()
        mock_client.post = post_mock
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = False

        with (
            patch(
                "mrag.generation.llm_client.httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch("mrag.generation.llm_client.asyncio.sleep", new=AsyncMock()),
        ):
            result = await client.generate("p")
        assert result == "hello world"

    async def test_malformed_response_raises(self) -> None:
        client = GroqLLMClient(
            api_url="https://api.example.com/v1",
            api_key="sk-test",
            max_retries=1,
            timeout=1,
        )
        post_mock = AsyncMock(
            return_value=_mk_httpx_response(200, {"unexpected": "shape"})
        )
        mock_client = AsyncMock()
        mock_client.post = post_mock
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = False

        with patch(
            "mrag.generation.llm_client.httpx.AsyncClient",
            return_value=mock_client,
        ), pytest.raises(ResponseGenerationError):
            await client.generate("p")
