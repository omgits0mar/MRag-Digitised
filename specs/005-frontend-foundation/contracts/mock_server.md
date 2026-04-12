# Contract: Mock Server (MSW)

**Module**: `frontend/src/mocks/`
**Files**: `browser.ts`, `handlers.ts`, `data.ts`

This contract defines the inventory of MSW handlers, the sample-data shapes they return, and the isolation guarantees that keep MSW out of production builds.

---

## 1. Activation

```ts
// frontend/src/main.tsx
if (import.meta.env.VITE_ENABLE_MOCK === "true") {
  const { worker } = await import("./mocks/browser");
  await worker.start({ onUnhandledRequest: "warn" });
}
```

- `onUnhandledRequest: "warn"` — any request to an endpoint without a handler logs a loud warning during dev so missing mocks are caught early.
- The dynamic import pattern lets Vite tree-shake the entire `mocks/` subtree when `VITE_ENABLE_MOCK` is statically `"false"` at build time.

---

## 2. Handler inventory (`handlers.ts`)

Each handler returns the sample payload defined in `data.ts`. All handlers respond with `Content-Type: application/json` and a realistic latency (40–180ms) via `delay()` to surface loading-state bugs in the UI.

| Endpoint | Method | Handler behaviour |
|----------|--------|-------------------|
| `/health` | GET | Returns `sampleHealthOk`. A second variant `sampleHealthDegraded` is exposed from `data.ts` so tests can override the handler to exercise the degraded branch. |
| `/ask-question` | POST | Returns `sampleQuestionResponse` echoing the request's `question` into the answer. Wired but not called by UI in this feature. |
| `/conversations` | GET | Returns `sampleConversationSummaries` (3 entries). |
| `/conversations/:id` | GET | Returns a `sampleConversationDetail` keyed by `:id`, or 404 with the backend error envelope if `:id` is not in the sample set. |
| `/conversations/:id` | DELETE | Returns 204. No state persisted across reloads — MSW is stateless per page load. |
| `/analytics` | GET | Returns `sampleAnalytics` regardless of `start`/`end` query params. |
| `/evaluate` | POST | Returns `sampleEvaluateResponse`. |
| `/models` | GET | Returns `sampleModels` (3 entries covering the three tiers). |

**Unhandled request policy**: any other path bubbles up as a console warning; this prevents silent "mock mode shows nothing" bugs when someone adds a new endpoint to `endpoints.ts` without updating handlers.

---

## 3. Sample data (`data.ts`)

Sample payloads MUST conform exactly to the TypeScript interfaces in `src/api/types.ts` so that a change to the interfaces forces a matching change here at compile time. The objects exported from `data.ts` are typed with `satisfies` so TypeScript flags drift immediately.

```ts
export const sampleHealthOk: HealthResponse = { ... } satisfies HealthResponse;
export const sampleHealthDegraded: HealthResponse = { ... } satisfies HealthResponse;
export const sampleConversationSummaries: ConversationSummary[] = [...] satisfies ConversationSummary[];
export const sampleConversationDetail: Record<string, ConversationDetail> = { ... };
export const sampleAnalytics: AnalyticsResponse = { ... } satisfies AnalyticsResponse;
export const sampleEvaluateResponse: EvaluateResponse = { ... } satisfies EvaluateResponse;
export const sampleQuestionResponse: QuestionResponse = { ... } satisfies QuestionResponse;
export const sampleModels: ModelInfo[] = [...] satisfies ModelInfo[];
```

**Content guidelines**:

- Sample `ConversationSummary.title` values are realistic natural-language titles (not "Untitled 1"), to exercise truncation and long-title overflow in the sidebar.
- `sampleQuestionResponse.sources` has at least 3 entries spanning different `relevanceScore` tiers (> 0.7, 0.4–0.7, < 0.4) so Feature 006's `RelevanceBar` renders all colour bands.
- `sampleAnalytics.queriesByDay` covers 30 days so Feature 007's dashboard renders a full time series.
- `sampleModels` includes one of each tier (`fast`, `balanced`, `quality`).

---

## 4. Test-mode usage (`frontend/tests/setup.ts`)

Tests use MSW's node server (`setupServer`) rather than the browser worker:

```ts
import { setupServer } from "msw/node";
import { handlers } from "@/mocks/handlers";

export const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

Individual tests override handlers via `server.use(http.get("/health", () => HttpResponse.json(sampleHealthDegraded)))` to exercise specific branches.

`onUnhandledRequest: "error"` is stricter than the browser's `"warn"` — in tests, any unmocked request is a hard failure.

---

## 5. Production isolation (FR-033)

Three enforcement points:

1. **Dynamic import**: MSW is only imported when `VITE_ENABLE_MOCK === "true"`. When the env var is `"false"` at build time, Vite eliminates the branch.
2. **CI env**: the production build step runs with `VITE_ENABLE_MOCK=false`, so mocks are dead code.
3. **Build-output grep**: `npm run build:check` greps the contents of `dist/` for `mockServiceWorker`, the string `from "msw"`, and `@mswjs`. Any match fails the build. This runs after `npm run build` in CI.

Additionally, `mockServiceWorker.js` (the worker script that MSW 2 expects to serve from the app origin) MUST NOT be copied into `public/` in production; it lives only in `public/` during dev and is `.gitignore`d for prod builds (and removed from `dist/` by an explicit post-build step).

---

## 6. Consistency guarantee

A future change to backend schemas (and consequently to `src/api/types.ts`) MUST update the sample payloads in `data.ts`. The `satisfies` annotations make this a compile-time requirement. There is no runtime schema validator in this feature — the compile-time guarantee plus the test-mode `onUnhandledRequest: "error"` is sufficient for the foundation.
