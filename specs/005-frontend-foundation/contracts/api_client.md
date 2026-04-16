# Contract: Frontend API Client

**Module**: `frontend/src/api/`
**Files**: `client.ts`, `endpoints.ts`, `types.ts`
**Consumes**: Phase 3 FastAPI (`src/mrag/api/`, Feature 004)

This contract defines the public surface of the frontend API layer: the Axios instance configuration, the typed endpoint functions, the error normalisation envelope, and the three backend addenda required before downstream features (006 Chat UI Core, 007 Advanced Chat Features) become fully wired.

---

## 1. Axios instance (`client.ts`)

```ts
export const apiClient: AxiosInstance; // singleton
```

**Configuration (set once at module load):**

| Property | Value | Source |
|----------|-------|--------|
| `baseURL` | `CONFIG.apiBaseUrl` | `config.ts` (from `VITE_API_BASE_URL`) |
| `timeout` | `CONFIG.apiRequestTimeoutMs` (default 30000) | `config.ts` (from `VITE_API_REQUEST_TIMEOUT_MS`) |
| `headers.Accept` | `application/json` | hard-coded |
| `headers.Content-Type` | `application/json` | hard-coded |
| `withCredentials` | `false` | no cookies in this feature |

**Request interceptor**

- Generates a per-request correlation id (UUID v4) and attaches it as the `X-Correlation-Id` header, available for matching backend logs to browser logs in Feature 006+.
- Emits a structured `logger.debug("api.request", { method, url, correlationId })`.

**Response interceptor (success path)**

- Emits `logger.debug("api.response", { status, url, durationMs, correlationId })`.
- Returns the raw Axios response; the endpoint wrapper converts to `ApiResult.ok(data)`.

**Response interceptor (error path)** — produces `ApiError`:

1. `AbortError` / `CanceledError` → `{ kind: "cancelled", message: "Request was cancelled" }`.
2. `ECONNABORTED` / timeout → `{ kind: "timeout", message: "Request timed out after ${timeoutMs}ms" }`.
3. Network error / no `response` → `{ kind: "network", message: "Backend is unreachable" }`.
4. HTTP response present:
    - If response body matches `BackendErrorEnvelope` (has `error`, `detail`, `status_code` keys of the right types) →
      `{ kind: "backend_error", status, message: envelope.error, detail: envelope.detail }`.
    - Otherwise → `{ kind: "network", message: "Unexpected response from backend (HTTP ${status})" }`.

`kind: "not_configured"` is never produced here; it is returned by endpoint wrappers when `config.ts` failed validation.

**Cancellation API**

```ts
export function createRequestHandle(): { signal: AbortSignal; cancel(): void };
```

Endpoint functions accept an optional `signal?: AbortSignal` argument forwarded to Axios. Callers obtain a signal from `createRequestHandle()` or `new AbortController()`.

---

## 2. Endpoint functions (`endpoints.ts`)

All functions return `Promise<ApiResult<T>>`. None throw; the discriminated union is the error channel. Every function respects `signal`.

### 2.1 `getHealth`

```ts
export function getHealth(opts?: { signal?: AbortSignal }): Promise<ApiResult<HealthResponse>>;
```

- Method / path: `GET /health`.
- Used by `useHealthCheck` on shell mount to render a health indicator in the Header.

### 2.2 `askQuestion`

```ts
export function askQuestion(
  request: QuestionRequest,
  opts?: { signal?: AbortSignal }
): Promise<ApiResult<QuestionResponse>>;
```

- Method / path: `POST /ask-question`.
- **This feature**: the function is exported and typed but **not called** from any component. Feature 006 wires it up. It is tested here to lock the request-serialisation shape.

### 2.3 `listConversations`

```ts
export function listConversations(opts?: { signal?: AbortSignal }): Promise<ApiResult<ConversationSummary[]>>;
```

- Method / path: `GET /conversations`.
- **Backend status**: pending backend addendum (T008-07 in source plan doc). Until the endpoint exists, MSW returns a sample list in mock mode, and against a real backend the client returns `{ kind: "backend_error", status: 404, ... }`.

### 2.4 `getConversation`

```ts
export function getConversation(id: string, opts?: { signal?: AbortSignal }): Promise<ApiResult<ConversationDetail>>;
```

- Method / path: `GET /conversations/{id}`.
- Same pending-backend caveat as `listConversations`.

### 2.5 `deleteConversation`

```ts
export function deleteConversation(id: string, opts?: { signal?: AbortSignal }): Promise<ApiResult<void>>;
```

- Method / path: `DELETE /conversations/{id}`.
- Same pending-backend caveat.
- On success, resolves with `{ kind: "ok", data: undefined }`.

### 2.6 `getAnalytics`

```ts
export function getAnalytics(
  range: { start: string; end: string },
  opts?: { signal?: AbortSignal }
): Promise<ApiResult<AnalyticsResponse>>;
```

- Method / path: `GET /analytics?start=...&end=...`.
- This endpoint exists today under Feature 004 (`src/mrag/api/routes/analytics.py`).

### 2.7 `runEvaluation`

```ts
export function runEvaluation(
  request: EvaluateRequest,
  opts?: { signal?: AbortSignal }
): Promise<ApiResult<EvaluateResponse>>;
```

- Method / path: `POST /evaluate`.
- Exists today under Feature 004.

### 2.8 `listModels`

```ts
export function listModels(opts?: { signal?: AbortSignal }): Promise<ApiResult<ModelInfo[]>>;
```

- Method / path: `GET /models`.
- **Backend status**: pending backend addendum (T007-10 in source plan doc). Against a real backend without the addendum, the client returns `{ kind: "backend_error", status: 404, message, detail }` which Feature 007's `ModelSelector` will treat as "fall back to static default".

---

## 3. Error taxonomy (summary)

| Scenario | `ApiError.kind` | How UI should respond |
|----------|-----------------|-----------------------|
| Backend returned `{error, detail, status_code}` 4xx/5xx | `backend_error` | Show `message`; if `status === 404` on a pending-addendum endpoint, treat as "feature unavailable". |
| Backend unreachable (DNS, offline, CORS preflight fail, HTTP no-response) | `network` | Show "Backend is unreachable" + Retry button. |
| Request exceeded `apiRequestTimeoutMs` | `timeout` | Show "Request timed out" + Retry. |
| User-initiated cancellation | `cancelled` | Silent; no UI message. |
| `config.ts` never produced a valid `CONFIG` | `not_configured` | Show `<EnvBanner/>` (already rendered by the root error boundary). |

The UI MUST NOT switch behaviour based on `status` codes alone except for `404 on pending-addendum endpoints`. All other distinctions (retryable vs. fatal) are made on `kind`.

---

## 4. Mock-mode semantics (FR-031/FR-032/FR-033)

When `CONFIG.enableMock === true`, `main.tsx` dynamically imports `./mocks/browser` and starts the MSW service worker **before** rendering `<App/>`. The API client is unchanged — MSW intercepts requests at the network layer, so `endpoints.ts` functions return `ApiResult.ok(...)` populated from `frontend/src/mocks/data.ts`.

**Production bundle guarantee**: Vite's dead-code elimination removes the dynamic import when `VITE_ENABLE_MOCK === "false"` at build time, and the `npm run build:check` script greps `dist/` for `mockServiceWorker.js` and `from "msw"` — a non-empty match fails the build.

Refer to `contracts/mock_server.md` for the handler inventory.

---

## 5. Backend addenda (out of scope for this feature, tracked for follow-up)

The following backend changes are required **before the downstream Phase 4 features are usable**. They modify Feature 004 (`src/mrag/api/`) and should be tracked as tasks against that feature, not this one. The contracts are documented here so the frontend API client is built to receive them.

| Id | Change | File |
|----|--------|------|
| BE-A1 | Add CORS origin (`http://localhost:5173`) to `Settings.api_cors_origins` default and `.env.example` | `src/mrag/config.py`, `.env.example` |
| BE-A2 | Extend `QuestionResponse` with `token_usage: TokenUsageSchema`, `latency: LatencyBreakdownSchema`, `is_fallback: bool`, `model_used: str` | `src/mrag/api/schemas.py` |
| BE-A3 | Add `GET /models` endpoint returning `List[ModelInfo]` from static config | `src/mrag/api/routes/models.py` (new) |
| BE-A4 | Add `GET /conversations`, `GET /conversations/{id}`, `DELETE /conversations/{id}` | `src/mrag/api/routes/conversations.py` (new) |

**Frontend compatibility**: the types declared in `types.ts` mark addendum-dependent fields as optional (`?:`). Components that need them (Feature 006+) will check for presence and render fallback UI ("—") when missing. This feature's code does not block on the addenda landing.
