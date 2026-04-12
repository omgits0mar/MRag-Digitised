# Data Model: Frontend Foundation & Dev Environment

**Branch**: `005-frontend-foundation` | **Date**: 2026-04-12 | **Plan**: `plan.md`

This document specifies the TypeScript types and in-memory / `localStorage` shapes used by the frontend foundation. It covers (a) DTOs that mirror the backend Phase 3 Pydantic schemas, (b) the client-side `ApiResult` / `ApiError` normalisation envelope, (c) the store state shapes, and (d) the persisted preference schema.

All interfaces live under `frontend/src/api/types.ts`, `frontend/src/stores/*`, or `frontend/src/config.ts`; paths are called out per section.

---

## 1. Backend-mirrored DTOs (`frontend/src/api/types.ts`)

These interfaces mirror the Pydantic models exposed by Feature 004's FastAPI layer. Any backend schema change surfaces here as a TypeScript compile-time error, satisfying SC-010.

### 1.1 `HealthResponse`

Mirrors `src/mrag/api/schemas.py::HealthResponse`.

```ts
export interface HealthResponse {
  status: "ok" | "degraded" | "down";
  uptimeSeconds: number;
  dependencies: {
    vectorStore: "ok" | "down";
    llm: "ok" | "down" | "unknown";
    database: "ok" | "down";
  };
  version: string;
}
```

### 1.2 `QuestionRequest` / `QuestionResponse`

Mirrors the Phase 3 `/ask-question` contract. The three fields marked `?` below are covered by backend-addendum #2 (see `plan.md`) and are optional in this feature's types so the client compiles cleanly whether the backend has shipped the addendum or not.

```ts
export interface QuestionRequest {
  question: string;
  conversationId?: string;
  topK?: number;
  scoreThreshold?: number;
  temperature?: number;
  model?: string;
}

export interface RetrievalSource {
  chunkId: string;
  chunkText: string;
  relevanceScore: number; // 0..1
  docId: string;
  questionType: string;
  domain: string;
  chunkIndex: number;
  totalChunks: number;
  originalQuestion?: string;
  originalAnswer?: string;
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

export interface LatencyBreakdown {
  embeddingMs: number;
  searchMs: number;
  llmMs: number;
  totalMs: number;
  cacheHit: boolean;
}

export interface QuestionResponse {
  answer: string;
  confidenceScore: number; // 0..1
  sources: RetrievalSource[];
  conversationId: string;
  tokenUsage?: TokenUsage;      // pending backend addendum #2
  latency?: LatencyBreakdown;   // pending backend addendum #2
  isFallback?: boolean;         // pending backend addendum #2
  modelUsed?: string;           // pending backend addendum #2
}
```

### 1.3 Conversations

```ts
export interface ConversationSummary {
  id: string;
  title: string;
  createdAt: string;    // ISO 8601
  updatedAt: string;    // ISO 8601
  messageCount: number;
}

export interface MessageRecord {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  createdAt: string;
  sources?: RetrievalSource[];
  tokenUsage?: TokenUsage;
  latency?: LatencyBreakdown;
}

export interface ConversationDetail extends ConversationSummary {
  messages: MessageRecord[];
}
```

### 1.4 Analytics

```ts
export interface AnalyticsResponse {
  rangeStart: string;
  rangeEnd: string;
  totalQueries: number;
  avgLatencyMs: number;
  cacheHitRate: number;     // 0..1
  queriesByDay: Array<{ date: string; count: number }>;
  tokenUsageByModel: Array<{ model: string; promptTokens: number; completionTokens: number }>;
  topDomains: Array<{ domain: string; count: number }>;
}
```

### 1.5 Evaluation

```ts
export interface EvaluateRequest {
  datasetPath?: string;
  kValues?: number[];
}

export interface EvaluateResponse {
  reportUrl: string;
  precisionAtK: Record<string, number>;
  recallAtK: Record<string, number>;
  mrr: number;
  bleu: number;
  rougeL: number;
  p50Ms: number;
  p95Ms: number;
  p99Ms: number;
}
```

### 1.6 Models listing (backend addendum #3)

```ts
export interface ModelInfo {
  name: string;
  provider: string;
  description: string;
  tier: "fast" | "balanced" | "quality";
}
```

### 1.7 Error envelope

Mirrors the Article VII envelope `{ "error": str, "detail": str, "status_code": int }`.

```ts
export interface BackendErrorEnvelope {
  error: string;
  detail: string;
  statusCode: number;
}
```

---

## 2. Client-side API result envelope (`frontend/src/api/client.ts`)

Every typed endpoint function returns a discriminated `ApiResult<T>`. Components never touch raw Axios responses.

```ts
export type ApiResult<T> =
  | { kind: "ok"; data: T }
  | { kind: "error"; error: ApiError };

export type ApiError =
  | { kind: "backend_error"; status: number; message: string; detail: string }
  | { kind: "network";        message: string }
  | { kind: "timeout";        message: string }
  | { kind: "cancelled";      message: string }
  | { kind: "not_configured"; message: string }; // raised when env validation fails before the call is made
```

**Invariants**

- `kind: "ok"` implies `data` is fully-typed, non-nullable `T`.
- `kind: "error"` always carries a human-readable `message` suitable to render directly in UI (FR-021, SC-006).
- `kind: "backend_error"` is reserved for responses with a parseable envelope; malformed 4xx/5xx fall back to `network` with the status-text message.
- `ApiError` never contains the raw Axios object; consumers cannot regress into stack-trace leakage.

---

## 3. Store state shapes

### 3.1 `chatStore` (`frontend/src/stores/chatStore.ts`)

```ts
export interface ChatMessage {
  id: string;                       // uuid generated client-side for user msgs; server-assigned for assistant msgs
  role: "user" | "assistant" | "system";
  content: string;
  createdAt: string;                // ISO 8601
  conversationId: string | null;    // null until first exchange lands
  sources?: RetrievalSource[];
  tokenUsage?: TokenUsage;
  latency?: LatencyBreakdown;
  confidence?: number;
  isFallback?: boolean;
  isStreaming?: boolean;
  error?: string;
}

export interface ChatStoreState {
  messages: ChatMessage[];
  activeConversationId: string | null;
  isStreaming: boolean;
  lastError: ApiError | null;
}

export interface ChatStoreActions {
  addMessage(message: ChatMessage): void;
  appendToLastAssistant(chunk: string): void; // used later by streaming; stubbed now
  setStreaming(value: boolean): void;
  setActiveConversation(id: string | null): void;
  setError(error: ApiError | null): void;
  clear(): void;
}
```

**Persistence**: none. `chatStore` is in-memory only. Chat history is rehydrated from the backend (Feature 006) rather than from browser storage.

**Transitions**:

- `clear()` resets `messages = []`, `isStreaming = false`, `lastError = null` but preserves `activeConversationId`.
- `setActiveConversation(id)` replaces `activeConversationId`; the caller is responsible for loading messages (Feature 006 concern).

### 3.2 `conversationStore` (`frontend/src/stores/conversationStore.ts`)

```ts
export interface ConversationStoreState {
  conversations: ConversationSummary[];
  activeId: string | null;
  isLoading: boolean;
  lastError: ApiError | null;
}

export interface ConversationStoreActions {
  loadConversations(): Promise<void>;
  selectConversation(id: string | null): void;
  deleteConversation(id: string): Promise<void>; // optimistic
  setError(error: ApiError | null): void;
}
```

**Persistence**: none (backend is the source of truth).

**Invariant**: `activeId`, if not null, must match some `conversations[i].id` **after** `loadConversations()` resolves; if the id disappears (deleted by another client), the store resets `activeId` to `null` and surfaces a non-blocking error.

### 3.3 `settingsStore` (`frontend/src/stores/settingsStore.ts`)

Persisted; uses Zustand `persist` middleware.

```ts
export type Theme = "system" | "light" | "dark";

export interface UserPreferenceSet {
  schemaVersion: 1;
  selectedModel: string;
  topK: number;               // [1..20], default 5
  scoreThreshold: number;     // [0..1], default 0.3
  temperature: number;        // [0..2], default 0.7
  theme: Theme;               // default "system"
}

export interface SettingsStoreState extends UserPreferenceSet {
  // fields identical to UserPreferenceSet; the persisted record is exactly the preference set
}

export interface SettingsStoreActions {
  setModel(model: string): void;
  setTopK(value: number): void;
  setScoreThreshold(value: number): void;
  setTemperature(value: number): void;
  setTheme(theme: Theme): void;
  resetDefaults(): void;
}
```

**Defaults** (from `config.ts` — never inlined in the store):

```ts
export const SETTINGS_DEFAULTS: UserPreferenceSet = {
  schemaVersion: 1,
  selectedModel: import.meta.env.VITE_DEFAULT_MODEL,
  topK: 5,
  scoreThreshold: 0.3,
  temperature: 0.7,
  theme: "system",
};
```

**Validation rules (FR-027 / FR-029)**

- `topK`: clamped to `[1, 20]` on `setTopK`; values outside range are rejected silently and a warning is logged.
- `scoreThreshold`: clamped to `[0, 1]`.
- `temperature`: clamped to `[0, 2]`.
- `selectedModel`: non-empty string; empty values fall back to `SETTINGS_DEFAULTS.selectedModel`.
- On hydrate: if the persisted blob is missing `schemaVersion`, has a higher `schemaVersion` than the app supports, or fails `JSON.parse`, the store initialises from `SETTINGS_DEFAULTS` and logs a one-time warning via `lib/logger.ts` (FR-029).

**Persistence key**: `mrag:settings:v1` in `localStorage`.

---

## 4. Env config (`frontend/src/config.ts`)

```ts
export interface EnvConfig {
  apiBaseUrl: string;              // required unless mock mode
  enableMock: boolean;
  defaultModel: string;            // required (seeds SETTINGS_DEFAULTS)
  enableStreaming: boolean;
  apiRequestTimeoutMs: number;     // default 30000
}

export interface EnvValidationError {
  missing: string[];
  invalid: Array<{ name: string; reason: string }>;
}
```

**Validation rules**

- `VITE_API_BASE_URL` is required unless `VITE_ENABLE_MOCK === "true"`.
- `VITE_DEFAULT_MODEL` is required always (seeds the settings defaults).
- `VITE_API_REQUEST_TIMEOUT_MS`, if present, must parse to a positive integer ≥ 1000 and ≤ 120000; otherwise default.
- `VITE_ENABLE_MOCK` and `VITE_ENABLE_STREAMING` parse as `"true" | "false"`; any other value is treated as `false` and logs a warning.

Validation runs once at module load (`config.ts` exports a frozen `CONFIG` object or throws an `EnvValidationError` caught by the root error boundary to render `<EnvBanner/>`).

---

## 5. Entity relationship (frontend-local)

```
EnvConfig ──seeds──▶ SettingsStore(UserPreferenceSet)
                         │
                         └──persists to──▶ localStorage["mrag:settings:v1"]

ApiResult<T> ──consumed by──▶ {useHealthCheck}   // this feature's only server-state hook
                              {loadConversations} // conversationStore action
                              {deleteConversation}// conversationStore action

ChatStore       (in-memory, session-lifetime)
ConversationStore(in-memory, session-lifetime, re-fetched from backend)
SettingsStore   (persisted)

No store imports another. Components compose via selectors.
```

---

## 6. Change-management notes

- **Backend schema drift**: adding or renaming a field on any Pydantic model in Feature 004 triggers a single TypeScript compile error in `frontend/src/api/types.ts`. This is the acceptance test for SC-010.
- **Adding a new preference**: bump `schemaVersion` to `2`, extend `UserPreferenceSet`, and add a migration branch in the `persist` middleware's `migrate` function that upgrades a `v1` blob forward. Never silently mutate existing persisted data.
- **Adding a new store**: new stores must be independently mountable (import from `stores/<name>` must not pull in another store's module). This keeps Article I (modular architecture) intact.
