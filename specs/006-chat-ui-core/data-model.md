# Data Model: Chat UI Core

**Branch**: `006-chat-ui-core` | **Date**: 2026-04-14 | **Plan**: `plan.md`

This document defines the frontend data shapes and state transitions needed for the core chat experience. It covers both backend-mirrored DTOs and the richer client-side message state required for streaming, citations, conversation switching, and inline error recovery.

The canonical implementation paths for these types are:

- `frontend/src/api/types.ts`
- `frontend/src/api/streaming.ts`
- `frontend/src/stores/chatStore.ts`
- `frontend/src/stores/conversationStore.ts`
- `frontend/src/hooks/useChatSession.ts`

---

## 1. `ChatMessage`

**Purpose**: A renderable transcript entry for the chat workspace.

```ts
export type ChatRole = "user" | "assistant";

export type ChatMessageStatus =
  | "complete"
  | "thinking"
  | "streaming"
  | "cancelled"
  | "interrupted"
  | "error";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  conversationId: string | null;
  content: string;
  createdAt: string;          // ISO 8601
  completedAt?: string;       // ISO 8601
  status: ChatMessageStatus;
  sources?: RetrievalSource[];
  tokenUsage?: TokenUsage;
  latency?: LatencyBreakdown;
  confidenceScore?: number;
  isFallback?: boolean;
  errorKind?: ApiError["kind"];
  errorMessage?: string;
}
```

**Validation rules**

- `role === "user"` messages must always be `status: "complete"` and must not carry `sources`, `tokenUsage`, or `latency`.
- `role === "assistant"` messages may start as `thinking`, then advance to `streaming` or any terminal status.
- `errorKind` is only valid when `status === "error"`.
- `completedAt` is required for `complete`, `cancelled`, `interrupted`, and `error` assistant messages.
- `content` may be empty only while an assistant message is still `thinking`.

**State transitions**

```text
assistant placeholder
thinking -> streaming -> complete
thinking -> complete                  (one-shot fallback path)
thinking|streaming -> cancelled
thinking|streaming -> interrupted
thinking|streaming -> error
error|interrupted|cancelled -> retried by reusing the same assistant slot or replacing it in-place
```

**Notes**

- Partial streamed content is preserved when transitioning to `interrupted` or `cancelled`.
- Low-confidence/fallback is orthogonal to status: a message can be `complete` and `isFallback === true`.

---

## 2. `ConversationRecord`

**Purpose**: Summary/detail model for the conversation rail, History page, and chat rehydration.

```ts
export interface ConversationRecord {
  id: string;
  title: string;
  createdAt: string;          // ISO 8601
  updatedAt: string;          // ISO 8601
  messageCount: number;
  messages?: ChatMessage[];   // present only for hydrated detail
  status?: "idle" | "loading" | "loaded" | "deleting";
}
```

**Validation rules**

- `title` is backend-authored and must be non-empty before rendering in the list.
- `messageCount >= 0`.
- `messages` is omitted in summary lists and present after detail load.
- `updatedAt >= createdAt`.

**State transitions**

```text
summary list item: idle -> loading -> loaded
active conversation: loaded -> deleting -> removed
new chat state: no active conversation selected until first successful answer yields/returns an id
```

**Notes**

- The frontend does not synthesize persistent titles or ids; those are backend/MSW responsibilities.
- When the backend has not yet shipped conversation routes, mock mode remains the only hydrated source.

---

## 3. `RetrievalSource`

**Purpose**: A single grounded source card linked to an assistant response.

```ts
export interface RetrievalSource {
  chunkId: string;
  docId: string;
  text: string;
  relevanceScore: number;     // 0..1
  domainTag?: string;
  questionType?: string;
  chunkIndex?: number;        // 1-based when shown to users
  totalChunks?: number;
  originalQuestion?: string;
  originalAnswer?: string;
}
```

**Validation rules**

- `0 <= relevanceScore <= 1`.
- `text` must be non-empty when the source exists.
- `chunkIndex` and `totalChunks` must appear together when available.
- Source card expansion is a derived UI flag, not persisted in the source object itself.

**Notes**

- The current backend only exposes `chunk_id`, `doc_id`, `text`, and `relevance_score`; the remaining fields are planned addenda and therefore optional.
- Citation `[N]` maps to the `N - 1` index in the assistant message’s `sources` array.

---

## 4. `TokenUsage`

**Purpose**: Token accounting shown in the assistant metadata footer.

```ts
export interface TokenUsage {
  promptTokens?: number;
  completionTokens?: number;
  totalTokens?: number;
}
```

**Validation rules**

- Every populated field must be a non-negative integer.
- `totalTokens` should be greater than or equal to `promptTokens + completionTokens` when all three are present.
- Missing fields are omitted, not filled with zero.

---

## 5. `LatencyBreakdown`

**Purpose**: Timing breakdown shown in the assistant metadata footer and expanded details.

```ts
export interface LatencyBreakdown {
  retrievalMs?: number;
  searchMs?: number;
  generationMs?: number;
  totalMs?: number;
  cacheHit?: boolean;
}
```

**Validation rules**

- Every populated timing field must be `>= 0`.
- `cacheHit` is optional; absence means “unknown”, not false.
- The UI may display only `totalMs` in compact mode and omit the breakdown rows when individual fields are missing.

**Notes**

- The current backend exposes only `response_time_ms`; richer latency fields are a planned schema extension.

---

## 6. `InFlightRequest`

**Purpose**: Ephemeral request metadata used to coordinate submit/cancel/retry without leaking transport objects into persisted store state.

```ts
export interface InFlightRequest {
  requestId: string;
  conversationId: string | null;
  userMessageId: string;
  assistantMessageId: string;
  submittedAt: string;        // ISO 8601
  mode: "stream" | "single";
  firstChunkAt?: string;      // ISO 8601
}
```

**Validation rules**

- Only one `InFlightRequest` may exist for the active conversation at a time.
- The live `AbortController` or cancellation handle is owned by the orchestration hook, not serialized into the store.
- `firstChunkAt` is only populated for streaming flows after the first token arrives.

**State transitions**

```text
idle -> in-flight(stream|single) -> terminal
terminal -> idle
```

**Terminal outcomes**

- success
- cancelled
- interrupted
- error

---

## 7. Derived UI state

These values are not first-class persisted entities but are required for rendering/spec compliance.

```ts
export interface ChatViewState {
  activeConversationId: string | null;
  focusedAssistantMessageId: string | null;
  jumpToLatestVisible: boolean;
  sourcePanelOpen: boolean;
  expandedSourceIds: string[];
}
```

**Rules**

- `focusedAssistantMessageId` defaults to the newest completed or in-progress assistant message.
- `sourcePanelOpen` is forced open when a citation is activated and the viewport is narrow.
- `jumpToLatestVisible` becomes true only when new content arrives while the user is not pinned to the bottom of the transcript.

---

## 8. Streaming event contract (frontend-consumed shape)

The streaming adapter consumes SSE-style events and reduces them into the entities above.

```ts
export type ChatStreamEvent =
  | { type: "chunk"; delta: string }
  | {
      type: "complete";
      answer: string;
      conversationId?: string | null;
      sources?: RetrievalSource[];
      tokenUsage?: TokenUsage;
      latency?: LatencyBreakdown;
      confidenceScore?: number;
      isFallback?: boolean;
    }
  | { type: "error"; error: BackendErrorEnvelope };
```

**Rules**

- `chunk` events append to the current assistant message and transition it to `streaming`.
- `complete` finalizes the message and backfills metadata fields.
- `error` preserves any partial content already rendered and transitions the message to `error` or `interrupted` depending on transport context.

---

## 9. Relationships summary

```text
ConversationRecord 1 ── * ChatMessage
ChatMessage (assistant) 1 ── 0..* RetrievalSource
ChatMessage (assistant) 1 ── 0..1 TokenUsage
ChatMessage (assistant) 1 ── 0..1 LatencyBreakdown
InFlightRequest 1 ── 1 user ChatMessage + 1 assistant ChatMessage placeholder
```

The key design rule is that the transcript remains the single source of truth for user-visible state, while API adapters and controller hooks are responsible for translating backend responses and stream events into these renderable entities.
