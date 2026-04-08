# Contract: Generation Pipeline

**Module**: `src/mrag/generation/`

## BaseLLMClient (ABC)

```python
from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> str:
        """Send prompt to LLM and return generated text.

        Args:
            prompt: User/assistant prompt content.
            system_prompt: Optional system instruction.
            temperature: Sampling temperature.
            max_tokens: Max response tokens.

        Returns:
            Generated text string.

        Raises:
            ResponseGenerationError: On API failure after retries.
        """
```

## GroqLLMClient

```python
class GroqLLMClient(BaseLLMClient):
    def __init__(
        self,
        api_url: str,
        api_key: str,
        model_name: str = "llama3-8b-8192",
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None: ...

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> str:
        """Call Groq OpenAI-compatible /v1/chat/completions endpoint."""
```

## PromptBuilder

```python
class PromptBuilder:
    def __init__(self, templates_dir: str = "prompts/templates") -> None: ...

    def build_qa_prompt(
        self,
        query: str,
        context_chunks: list[RetrievalResult],
        conversation_history: list[ConversationTurn] | None = None,
    ) -> str:
        """Render the Q&A prompt template with context.

        Hot-reloads template if file mtime has changed.

        Returns:
            Rendered prompt string.
        """

    def build_system_prompt(self) -> str:
        """Render the system instruction template."""
```

## ResponseValidator

```python
class ResponseValidator:
    def __init__(
        self,
        confidence_threshold: float = 0.3,
        alpha: float = 0.6,
    ) -> None: ...

    def validate(
        self,
        response_text: str,
        context_chunks: list[RetrievalResult],
        retrieval_scores: list[float],
    ) -> ValidationResult:
        """Score response confidence.

        confidence = alpha * mean(retrieval_scores) + (1-alpha) * tfidf_overlap

        Returns:
            ValidationResult with confidence score and is_confident flag.
        """
```

## FallbackHandler

```python
class FallbackHandler:
    def get_fallback_response(self, query: str) -> str:
        """Return a fallback response for low-confidence answers.

        Returns:
            Canned response indicating insufficient information.
        """
```

## GenerationPipeline

```python
class GenerationPipeline:
    def __init__(
        self,
        llm_client: BaseLLMClient,
        prompt_builder: PromptBuilder,
        validator: ResponseValidator,
        fallback_handler: FallbackHandler,
    ) -> None: ...

    async def generate_answer(
        self,
        query: str,
        retrieval_results: list[RetrievalResult],
        conversation_history: list[ConversationTurn] | None = None,
    ) -> GeneratedResponse:
        """Full generation pipeline.

        1. Build prompt from query + context
        2. Call LLM
        3. Validate response
        4. Return response or fallback

        Returns:
            GeneratedResponse with answer, confidence, sources, metrics.

        Raises:
            ResponseGenerationError: If LLM call fails and no fallback.
        """
```
