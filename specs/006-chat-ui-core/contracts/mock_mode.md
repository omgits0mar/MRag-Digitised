# Contract: Mock Mode for Chat UI Core

**Module**: `frontend/src/mocks/`  
**Files**: `data.ts`, `handlers.ts`, `browser.ts`

Feature 006 extends the Feature 005 mock layer so the full chat workspace is testable and demoable with no backend running.

---

## 1. Activation

Mock mode remains controlled by:

```text
VITE_ENABLE_MOCK=true
```

The browser worker still starts before React mounts, exactly as established in Feature 005. Production builds continue to run with `VITE_ENABLE_MOCK=false`.

---

## 2. Handler inventory

The existing handlers remain and are extended as follows:

| Endpoint | Method | Behaviour |
|----------|--------|-----------|
| `/health` | GET | Same as Feature 005. |
| `/ask-question` | POST | Returns a fully typed one-shot response for fallback mode. |
| `/ask-question/stream` | POST | Returns an SSE-style `ReadableStream` that emits `chunk` and `complete` events for normal requests. |
| `/conversations` | GET | Returns seeded conversation summaries. |
| `/conversations/:id` | GET | Returns seeded conversation detail with assistant metadata where available. |
| `/conversations/:id` | DELETE | Returns 204 and removes the conversation from the in-memory mock dataset for the current page session. |
| `/analytics` | GET | Same as Feature 005. |
| `/evaluate` | POST | Same as Feature 005. |
| `/models` | GET | Same as Feature 005. |

---

## 3. Scenario tags

The mock ask handlers inspect the submitted question text for deterministic scenario tags:

| Tag | Behaviour |
|-----|-----------|
| `[mock:fallback]` | Returns a completed assistant response with `is_fallback=true`, low confidence, and no sources. |
| `[mock:error]` | Returns a backend error envelope (`500`) for one-shot mode or an `error` event for streaming mode. |
| `[mock:timeout]` | Delays long enough for the client timeout path to fire. |
| `[mock:interrupt]` | Streams a few chunks, then closes the stream early to trigger the interrupted-message path. |
| `[mock:nosources]` | Returns a successful answer with an empty source list and explicit no-sources state. |

If no tag is present, the handlers return the normal happy-path response with citations, sources, and metadata.

---

## 4. Streaming payload shape

The streaming handler emits SSE-style frames compatible with `contracts/chat_api.md`:

```text
event: chunk
data: {"delta":"First part "}

event: chunk
data: {"delta":"second part "}

event: complete
data: {"answer":"First part second part","conversation_id":"conv-1","sources":[...],"token_usage":{...},"latency":{...},"confidence_score":0.93,"is_fallback":false}
```

Tests may override the handler with custom streams, but the default fixtures must already cover:

- happy path
- interrupted stream
- backend error
- fallback/no-sources

---

## 5. Sample data requirements

`data.ts` must export typed fixtures for:

- conversation summaries and details
- assistant messages with citations
- source cards containing varied relevance scores
- token usage and latency payloads
- low-confidence/fallback response variants

The fixtures should continue to use `satisfies` so schema drift in `src/api/types.ts` fails at compile time.

---

## 6. Test-mode usage

The Vitest `setupServer` flow from Feature 005 remains unchanged, but tests are expected to override chat scenarios directly when precision matters:

```ts
server.use(
  http.post("*/ask-question/stream", () => {
    return new HttpResponse(customReadableStream, {
      headers: { "Content-Type": "text/event-stream" },
    });
  }),
);
```

`onUnhandledRequest: "error"` remains mandatory in tests.

---

## 7. Production isolation

Feature 005’s isolation guarantees continue to apply:

1. Dynamic import behind `VITE_ENABLE_MOCK`.
2. `npm run build` forces `VITE_ENABLE_MOCK=false`.
3. `npm run build:check` fails if MSW artifacts leak into `dist/`.

Feature 006 must not add any debug UI or scenario controls that are visible outside mock mode.
