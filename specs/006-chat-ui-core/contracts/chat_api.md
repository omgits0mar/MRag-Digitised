# Contract: Chat API and Streaming Boundary

**Module**: `frontend/src/api/`  
**Files**: `client.ts`, `endpoints.ts`, `types.ts`, `streaming.ts`  
**Consumes**: Phase 3 FastAPI app under `src/mrag/api/`

This contract defines the only backend integration surface Feature 006 is allowed to use. All chat, conversation, retry, and streaming behaviour must go through this seam.

---

## 1. Core rule

- Components, hooks outside `frontend/src/api/`, and stores MUST NOT call `fetch` or `axios` directly.
- JSON request/response endpoints live in `endpoints.ts`.
- Streaming lives in `streaming.ts`.
- Both surfaces return typed values that reduce into the shared `ApiError` taxonomy and `ChatMessage` state model.

---

## 2. Existing one-shot endpoints

These continue to use the Axios-based client from Feature 005.

### 2.1 `POST /ask-question`

```ts
export interface QuestionRequest {
  question: string;
  conversation_id?: string | null;
  expand?: boolean;
  temperature?: number;
  max_tokens?: number;
}

export interface QuestionResponse {
  answer: string;
  confidence_score: number;
  is_fallback: boolean;
  sources: SourceResponse[];
  response_time_ms: number;
  conversation_id?: string | null;
  token_usage?: TokenUsage;
  latency?: LatencyBreakdown;
}
```

**Frontend expectations**

- Always available as the fallback path when streaming is unavailable.
- If `conversation_id` is absent in the request, the backend should eventually return a newly created id; until that addendum lands, the frontend keeps the conversation active only in session/mocks.
- `token_usage` and `latency` are optional because the current backend schema does not yet expose them.

### 2.2 Conversation endpoints

```ts
GET    /conversations
GET    /conversations/{id}
DELETE /conversations/{id}
```

**Status**: required by Feature 006, but not currently implemented in the checked-in FastAPI app.

**Frontend expectations**

- In mock mode, these endpoints are fully implemented by MSW.
- Against the real backend, a 404 from these paths should be interpreted as “pending backend addendum”, not as a frontend contract bug.

### 2.3 Shared error taxonomy

All failures reduce to:

```ts
export type ApiError =
  | { kind: "backend_error"; status: number; message: string; detail: string }
  | { kind: "network"; message: string }
  | { kind: "timeout"; message: string }
  | { kind: "cancelled"; message: string }
  | { kind: "not_configured"; message: string };
```

The chat UI renders these inline per assistant message. `cancelled` is a user action, not a backend fault.

---

## 3. Streaming endpoint contract

### 3.1 Route

```text
POST /ask-question/stream
Content-Type: application/json
Accept: text/event-stream
```

### 3.2 Request body

Same payload shape as `QuestionRequest`.

### 3.3 Response media type

```text
text/event-stream
```

### 3.4 Event inventory

The frontend streaming parser expects newline-delimited SSE events of the form:

```text
event: chunk
data: {"delta":"..."}

event: complete
data: {"answer":"...","conversation_id":"...","sources":[...],"token_usage":{...},"latency":{...},"confidence_score":0.91,"is_fallback":false}

event: error
data: {"error":"...","detail":"...","status_code":500}
```

**Semantics**

- `chunk`: append `delta` to the active assistant message and transition it to `streaming`.
- `complete`: finalize the assistant message, backfill metadata, and clear in-flight state.
- `error`: preserve any partial content already rendered, transition the assistant message to `error`, and expose Retry.

**Transport failure semantics**

- If the HTTP request returns `404`, `405`, or `501`, `streaming.ts` returns a typed “stream unavailable” result and the caller falls back to `POST /ask-question`.
- If the stream connection drops after at least one chunk, the frontend marks the message `interrupted`.
- If the client timeout elapses before completion, the frontend marks the message `error` with `kind: "timeout"`.

### 3.5 Adapter surface

`streaming.ts` exposes a callback-driven helper similar to:

```ts
export interface StreamAnswerOptions {
  signal: AbortSignal;
  onChunk(delta: string): void;
  onComplete(payload: StreamCompletePayload): void;
}

export type StreamAnswerResult =
  | { kind: "complete" }
  | { kind: "unavailable" }
  | { kind: "error"; error: ApiError };
```

The adapter must not mutate stores directly; it only emits typed events.

---

## 4. Conversation payload expectations

The frontend expects these real-backend shapes once the addenda land:

```ts
export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  sources?: SourceResponse[];
  token_usage?: TokenUsage;
  latency?: LatencyBreakdown;
  confidence_score?: number;
  is_fallback?: boolean;
}

export interface ConversationDetail extends ConversationSummary {
  messages: ConversationMessage[];
}
```

The checked-in backend currently persists conversation turns but only stores question/response text. Source and metadata fields are therefore optional even after the conversation routes appear.

---

## 5. Backend addenda required for real parity

| Id | Change | Why Feature 006 needs it |
|----|--------|--------------------------|
| BE-006-A1 | `POST /ask-question/stream` | Required for true token-by-token streaming. |
| BE-006-A2 | New-conversation id creation on ask routes | Required for “New Chat” to become a real persisted conversation. |
| BE-006-A3 | `GET/DELETE /conversations*` routes | Required for conversation list, load, and deletion against the real backend. |
| BE-006-A4 | Optional assistant metadata in conversation detail | Required for revisiting prior conversations with sources and metrics when persisted. |
| BE-006-A5 | CORS origin wiring | Required for local real-backend dev workflow. |

The frontend must remain functional without these addenda by using mock mode and the documented one-shot degradation path.
