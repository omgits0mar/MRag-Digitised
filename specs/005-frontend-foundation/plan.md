# Implementation Plan: Frontend Foundation & Dev Environment

**Branch**: `005-frontend-foundation` | **Date**: 2026-04-12 | **Spec**: specs/005-frontend-foundation/spec.md
**Input**: Feature specification from `/specs/005-frontend-foundation/spec.md`
**Constitution Version**: 1.0.0
**Source plan document**: `docs/mrag-phase4-frontend-plan.md` (Phase 4, Feature 010)

## Summary

This feature stands up the Phase 4 frontend: a new `frontend/` sub-project at the repository root containing a Vite + React 18 + TypeScript 5 single-page app, a typed API client that mirrors the Phase 3 FastAPI contracts, Zustand-based global state with `localStorage` preference persistence, a responsive shell (Sidebar + Header + content region) using Tailwind CSS and `shadcn/ui` primitives, MSW-backed mock mode for backend-independent development, and the full quality baseline (ESLint, Prettier, Vitest, React Testing Library, Playwright wiring, Lighthouse budgets, accessibility checks). No chat, streaming, or conversation UX is delivered here — those are downstream features (planned as Features 006 Chat UI Core and 007 Advanced Chat Features per the source plan doc). The backend is **not** modified by this feature; a small set of backend addenda (CORS for the frontend origin, a `/models` listing endpoint, response-schema extensions for token usage / latency / fallback flag) is called out at the end of this plan as follow-up work for the existing Phase 3 modules. Every surface of this feature treats the backend as an external contract, so frontend work can proceed against MSW mocks while the addenda are being landed.

## Technical Context

**Language/Version**: TypeScript 5.4+ (strict mode, `noUncheckedIndexedAccess: true`), Node.js 20 LTS for tooling
**Primary Dependencies**: react 18.3, react-dom 18.3, react-router-dom 6.x, vite 5.x, @vitejs/plugin-react 4.x, tailwindcss 3.x, autoprefixer, postcss, shadcn/ui primitives (radix-ui + class-variance-authority + tailwind-merge + lucide-react icons), zustand 4.x, axios 1.x, msw 2.x; dev: eslint 9.x with `@typescript-eslint`, eslint-plugin-react, eslint-plugin-react-hooks, eslint-plugin-jsx-a11y, prettier 3.x, vitest 1.x, @testing-library/react 16.x, @testing-library/jest-dom, @testing-library/user-event, jsdom, @playwright/test 1.x (wired but with no specs in this feature), @axe-core/react for automated a11y checks
**Storage**: Browser `localStorage` for `User Preference Set` only (selected model, top-k, score threshold, temperature, theme, schema version). No IndexedDB, no cookies, no server-side session storage. Chat state and conversation state live in-memory for the session; they are re-hydrated from the backend (Feature 004 database) in downstream chat features, not here.
**Testing**: Vitest + React Testing Library for unit and component tests (jsdom env), MSW for API-boundary tests, `@axe-core/react` for automated a11y assertions in component tests, `@playwright/test` installed and configured but with no end-to-end specs in this feature (Phase 4 feature 007 owns the e2e suite).
**Target Platform**: Modern evergreen browsers — latest two versions of Chrome, Edge, Firefox, Safari. ES2020+ baseline. Served as static assets (Vite build output) from any static host or via the FastAPI static mount in later deployment work.
**Project Type**: Web application frontend (SPA). Sits alongside the existing Python backend; consumes the Phase 3 FastAPI service (Feature 004 in this repo, i.e. `src/mrag/api/`) over HTTP.
**Performance Goals**: Lighthouse performance score ≥ 85 on the empty shell (SC-004); Largest Contentful Paint ≤ 3s on a mid-range laptop over typical home broadband (SC-004); First Input Delay ≤ 100ms; initial JS bundle (gzipped) ≤ 200 KB for the shell route (route-splitting keeps Chat/History/Settings out of the initial chunk); cold `npm run dev` boot ≤ 5s on M-series hardware; `npm run build` ≤ 30s.
**Constraints**: Strict TS (`any` prohibited in baseline scaffold per FR-007); zero ESLint violations; zero axe critical violations on the empty shell; WCAG AA contrast in both themes (FR-036); layout works 360px–2560px (FR-015); `npm run dev` and all test commands MUST succeed with no backend running (mock mode); build output MUST NOT contain MSW (FR-033).
**Scale/Scope**: Single SPA entrypoint; ~15 source files in this feature (3 pages, 3 layout components, 3 stores, 3 api module files, 1 router, 1 app entry, 1 config module, 1 MSW handlers file); tests per module. Handles a single implicit user (no auth in this feature — see Assumptions in spec).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution was written for the Python backend and Phases 1–3. Several articles apply verbatim to any module of the system; a few (IV, V) apply only to the retrieval/generation path and are therefore marked N/A for a frontend-only feature. Where an article mandates a specific Python tool, the frontend adopts the documented intent of the article using the nearest TypeScript/web equivalent.

| Article | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| I — Modular Architecture | Independent modules with explicit I/O contracts | PASS | Frontend is a new independent module (`frontend/`) that talks to the backend only over the HTTP contract defined in Feature 004. Within the frontend, each concern (API client, stores, layout, pages, mocks) is its own folder with a clear boundary; no store imports from another store; components never import from pages; mocks are isolated to `frontend/src/mocks/` and are stripped from production builds. |
| II — Data Integrity & Preprocessing | Validation at every boundary | PASS | The API integration layer is the single boundary for backend data; it normalises errors (FR-021) and keeps response shapes in types so any backend schema drift fails at compile time in one place (SC-010). Persisted preferences are schema-versioned and fall back to defaults on corruption (FR-029). |
| III — Multilingual-First Design | UTF-8 throughout, no ASCII-only assumptions | PASS | All request/response bodies are JSON with explicit `Accept: application/json` and the browser's native UTF-8 decoding; no byte-level string handling anywhere. UI chrome is English-only in this feature (documented assumption in spec) but any multilingual payload returned by the backend will round-trip intact. |
| IV — Retrieval Quality > Speed | Retrieval correctness gating | N/A | Frontend does not perform retrieval. The user-facing knobs (top-k, score threshold, temperature) are forwarded as parameters to the backend in downstream chat features; this foundation feature only stores them. |
| V — LLM as Replaceable Contract | Unified LLM interface, externalised prompts | N/A | Frontend does not talk to any LLM directly. All LLM interaction is via the backend's `POST /ask-question` contract. |
| VI — Testing & Evaluation | Unit + integration + quality gates | PASS | Vitest + React Testing Library cover components, stores, hooks; MSW-based tests cover the API integration layer; `@axe-core/react` asserts a11y in component tests; Playwright is wired (config, directory, CI placeholder) but end-to-end specs are explicitly deferred to Phase 4 feature 007 per the source plan doc. Every module delivered here has at least one test file in this feature. |
| VII — API Design & Error Handling Standards | FastAPI + Pydantic contract | PASS (consumer side) | Frontend is the consumer side of the Article VII contract. It mirrors the backend's Pydantic schemas in TypeScript interfaces generated/hand-written in `frontend/src/api/types.ts`, and normalises errors into the `{ error, detail, status_code }` envelope exactly as the backend emits it. Backend-side additions needed for the frontend (CORS for the FE origin, `/models`, response-schema extensions) are called out as Phase 3 addenda — they modify Feature 004 and are out of scope for this feature's code but listed below so they can be picked up as follow-ups. |
| VIII — Performance & Caching Discipline | Metrics on every request, measured optimisation | PASS | Performance budgets are measured (Lighthouse ≥ 85, LCP ≤ 3s, bundle ≤ 200 KB gzipped). The API client emits a per-request duration log (via Axios interceptor) for observability. Browser-side caching is limited to `localStorage` preference persistence (explicit invalidation: schema-version bump → fall back to defaults). No ad-hoc caches that could go stale silently. |
| IX — Code Quality & Development Standards | Type hints, formatting, linting, structured logging, env vars for secrets | PASS (TypeScript equivalents) | The article mandates Python 3.10+ / black / ruff / docstrings / structlog / env vars. For the frontend we adopt the documented *intent*: TypeScript 5 strict (type hints), Prettier (formatting), ESLint with TS+React+a11y plugins (linting), JSDoc on exported functions (documentation), a tiny structured logger utility wrapping `console` at a single level (structured logging), and `import.meta.env.VITE_*` for all configuration (env vars). No secrets are needed in this feature; `.env` is gitignored. |
| X — Documentation Separation of Concerns | Spec = WHAT, Plan = HOW | PASS | `spec.md` intentionally contains no library names; every library mentioned in this feature appears here in `plan.md` for the first time. The source plan document under `docs/` is design input, not itself a speckit artefact. |

**No violations.** Articles IV and V are marked N/A because this feature is strictly frontend scaffolding; they become directly relevant again in Feature 006 (Chat UI Core), where retrieval knobs and LLM responses are surfaced to users. Article IX is satisfied by mapping each Python-specific requirement to its TypeScript equivalent; this mapping is documented in the Constitution Check row above so reviewers can follow the substitution.

## Project Structure

### Documentation (this feature)

```text
specs/005-frontend-foundation/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── api_client.md           # Frontend API client contract + typed endpoints
│   ├── state_stores.md         # Zustand store contracts (chat/conversation/settings)
│   └── mock_server.md          # MSW handler contract and mock data shape
├── checklists/
│   └── requirements.md  # Spec quality checklist (already passing)
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
frontend/                              # NEW — Phase 4 root
├── package.json                       # deps pinned; scripts: dev, build, preview, test, test:watch, lint, format, typecheck
├── package-lock.json
├── tsconfig.json                      # strict: true, noUncheckedIndexedAccess: true, target ES2020
├── tsconfig.node.json                 # for vite.config.ts typechecking
├── vite.config.ts                     # React plugin, path aliases (@/ → src/), test config (vitest env=jsdom)
├── tailwind.config.ts                 # content globs, dark mode class-based, shadcn/ui theme tokens
├── postcss.config.js
├── .eslintrc.cjs                      # TS + React + hooks + jsx-a11y, Prettier-compatible
├── .prettierrc
├── .env.example                       # VITE_API_BASE_URL, VITE_ENABLE_MOCK, VITE_DEFAULT_MODEL, VITE_ENABLE_STREAMING
├── .gitignore                         # node_modules, dist, coverage, .env
├── index.html                         # Vite entry
├── playwright.config.ts               # Wired, no specs — Feature 007 owns e2e
├── public/
│   └── favicon.svg
└── src/
    ├── main.tsx                       # React root, router, MSW bootstrap in mock mode
    ├── App.tsx                        # <AppShell>/<Outlet>; wraps router
    ├── config.ts                      # Typed env loader with startup validation (FR-010)
    ├── router.tsx                     # createBrowserRouter; lazy route imports for Chat/History/Settings
    │
    ├── api/
    │   ├── client.ts                  # Axios instance + interceptors; ApiError normalisation + cancellation
    │   ├── endpoints.ts               # Typed functions: health, askQuestion, listConversations, getConversation, deleteConversation, getAnalytics, runEvaluation
    │   └── types.ts                   # TS interfaces mirroring Phase 3 Pydantic schemas
    │
    ├── stores/
    │   ├── chatStore.ts               # Zustand: messages, isStreaming, activeConversationId, error, actions
    │   ├── conversationStore.ts       # Zustand: conversations, activeId, loadConversations(), deleteConversation()
    │   └── settingsStore.ts           # Zustand + persist middleware: selectedModel, topK, scoreThreshold, temperature, theme
    │
    ├── components/
    │   └── layout/
    │       ├── AppShell.tsx           # Sidebar + Header + <Outlet/>
    │       ├── Sidebar.tsx            # Nav (Chat/History/Settings), collapsed drawer on ≤768px
    │       ├── Header.tsx             # Brand + hamburger + placeholder model-selector slot
    │       ├── ThemeProvider.tsx      # Reads settingsStore.theme + system preference → toggles `dark` class on <html>
    │       └── EnvBanner.tsx          # Shown only if config validation fails (FR-010)
    │
    ├── pages/
    │   ├── ChatPage.tsx               # Placeholder: "Chat UI is not yet built (Feature 006)"; welcomes user + links to docs
    │   ├── HistoryPage.tsx            # Placeholder: "History will be built in Feature 006"
    │   └── SettingsPage.tsx           # Placeholder: "Settings will be built in Feature 007"
    │
    ├── hooks/
    │   └── useHealthCheck.ts          # Calls health endpoint on mount; surfaces status in Header
    │
    ├── mocks/
    │   ├── browser.ts                 # setupWorker() — only loaded when VITE_ENABLE_MOCK === "true"
    │   ├── handlers.ts                # MSW handlers for health, ask-question, conversations, analytics, evaluate
    │   └── data.ts                    # Sample payloads (one question w/ sources, three conversations, analytics snapshot)
    │
    ├── lib/
    │   ├── logger.ts                  # Tiny structured logger (console.* with level + context object) — Article IX intent
    │   └── cn.ts                      # className joiner (shadcn/ui convention)
    │
    ├── styles/
    │   └── globals.css                # Tailwind base/components/utilities + CSS vars for shadcn/ui theme tokens
    │
    └── types/
        └── env.d.ts                   # ImportMetaEnv typing for VITE_* vars

frontend/tests/                        # Co-located test tree
├── unit/
│   ├── api/
│   │   ├── test_client.ts             # Error normalisation, timeout, cancellation, mock-mode routing
│   │   └── test_endpoints.ts          # Each endpoint function produces correct request shape
│   ├── stores/
│   │   ├── test_chatStore.ts          # Actions produce expected state transitions
│   │   ├── test_conversationStore.ts  # Loader + delete optimistic update
│   │   └── test_settingsStore.ts      # Persistence + schema-version fallback
│   └── lib/
│       └── test_logger.ts
├── integration/
│   ├── test_app_shell.tsx             # Renders shell at 360/768/1280/2560; keyboard nav; axe assertions
│   ├── test_routing.tsx               # Navigates Chat/History/Settings; URL updates; no full reload
│   ├── test_env_banner.tsx            # Missing VITE_API_BASE_URL surfaces banner
│   └── test_mock_mode.tsx             # With MSW enabled, all views render without hitting a real backend
├── setup.ts                           # RTL + jest-dom + MSW server (node) setup
└── e2e/                               # Directory reserved for Feature 007; currently empty with a README

backend/ — NOT modified by this feature
(Phase 3 Feature 004 `src/mrag/api/` remains the integration target; a small set of addenda is listed below but tracked as follow-up work, not inside this feature.)
```

**Structure Decision**: Introduce a sibling `frontend/` tree at the repository root, peer to the existing `src/mrag/` backend package. The two trees share the repo but have independent toolchains (pip + pytest on the backend side, npm + vitest on the frontend side) — there is no monorepo package manager (Nx / Turborepo / pnpm workspaces) because the two sides do not share TypeScript code and the complexity of a workspace tool is not justified for one frontend and one backend. The frontend never imports from the backend tree and vice versa; their only contract is the HTTP API defined in Feature 004. Co-locating tests inside `frontend/tests/` (rather than next to each source file) matches the existing `tests/` convention used by the Python side of the repo, keeping the mental model consistent across the two trees.

**Backend integration target**: Phase 3 FastAPI app at `src/mrag/api/` (Feature 004). No source changes to the backend in this feature. Three backend addenda are needed before downstream Phase 4 features (not this one) are useful:

1. **CORS origin allowlist** — add the frontend dev-server origin to `Settings.api_cors_origins` (existing field) and document it in `.env.example`. Today the backend already has CORS middleware wired; it just needs the origin added. This is a config change, not a code change.
2. **Response schema extensions** — extend `QuestionResponse` to include `token_usage: TokenUsageSchema`, `latency: LatencyBreakdownSchema`, `is_fallback: bool`, `model_used: str`. Feature 006 (Chat UI Core) depends on these; this foundation feature compiles against optional-marked versions of the types and degrades gracefully if the backend hasn't shipped them yet.
3. **`GET /models` endpoint** — lists available LLM models with `name`, `provider`, `description`, `tier`. Feature 007 depends on this; the foundation feature's API client exposes the typed function but will return an empty list if the endpoint 404s (FR-024 distinguishes "endpoint missing" from generic errors).

These three addenda are written into `contracts/api_client.md` with `status: pending-backend` so the frontend can proceed against MSW mocks without waiting.

## Architecture

### Runtime & data flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Browser tab                                                                 │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Vite bundle (main.tsx → App.tsx)                                        │ │
│ │                                                                         │ │
│ │  ┌───────────────────┐      ┌───────────────────┐                       │ │
│ │  │ config.ts         │      │ ThemeProvider     │                       │ │
│ │  │ validates env     │      │ syncs html.dark   │                       │ │
│ │  │ (FR-010)          │      │ from settings     │                       │ │
│ │  └─────────┬─────────┘      └───────────────────┘                       │ │
│ │            │                                                            │ │
│ │            ▼                                                            │ │
│ │  ┌───────────────────┐      ┌───────────────────┐    ┌────────────────┐ │ │
│ │  │ AppShell          │──▶──▶│ <Outlet/>         │    │ Zustand stores │ │ │
│ │  │ Sidebar + Header  │      │ Lazy pages        │    │ chat · conv.   │ │ │
│ │  └─────────┬─────────┘      └─────────┬─────────┘    │ settings       │ │ │
│ │            │ useHealthCheck           │              │ (persist ↔ LS) │ │ │
│ │            │                          │              └────────┬───────┘ │ │
│ │            ▼                          ▼                       │         │ │
│ │        ┌────────────────────────────────────────────────┐     │         │ │
│ │        │ src/api/ (client + endpoints + types)          │◀────┘         │ │
│ │        │ Axios → normalise → ApiResult<T>               │               │ │
│ │        └───────────────────────┬────────────────────────┘               │ │
│ │                                │                                        │ │
│ │      VITE_ENABLE_MOCK=true? ───┤                                        │ │
│ │                    ┌───────────┴───────────┐                            │ │
│ │                    ▼                       ▼                            │ │
│ │           ┌──────────────────┐    ┌──────────────────┐                  │ │
│ │           │ MSW service      │    │ real fetch to    │                  │ │
│ │           │ worker (handlers)│    │ VITE_API_BASE_URL│                  │ │
│ │           └──────────────────┘    └────────┬─────────┘                  │ │
│ └─────────────────────────────────────────────│──────────────────────────┘ │
└───────────────────────────────────────────────│─────────────────────────────┘
                                                │
                                                ▼
                                  ┌─────────────────────────────┐
                                  │ Phase 3 FastAPI (Feature 004│
                                  │ `src/mrag/api/`)            │
                                  └─────────────────────────────┘
```

**Critical flow invariants**

1. **Single integration seam (FR-018, SC-005)**: Every HTTP call originates from `src/api/endpoints.ts` calling the Axios instance in `src/api/client.ts`. An ESLint rule (`no-restricted-imports`) forbids importing `axios` or `fetch` directly from anywhere else under `src/`. The SC-005 verification is a repo-wide lint check.
2. **Mock-mode isolation (FR-033)**: MSW is dynamically imported at runtime behind `if (import.meta.env.VITE_ENABLE_MOCK === "true") { await import("./mocks/browser").then(({ worker }) => worker.start()) }`. Tree-shaking removes the branch from production builds when the env var is set to `"false"` at build time, and the build script asserts (via a grep-based check on the generated bundle) that `mockServiceWorker.js` is not present in `dist/`.
3. **Config validation at startup (FR-010)**: `config.ts` reads `import.meta.env`, validates required keys via a hand-rolled typed reader (no zod dependency needed for 4 vars), and throws before React mounts if a required key is missing. The error boundary at the root catches this and renders `<EnvBanner/>` with actionable text ("Set `VITE_API_BASE_URL` in `frontend/.env`") instead of a white screen.
4. **Error normalisation (FR-021, FR-024)**: The Axios response interceptor maps every failure into a discriminated union:
   - `{ kind: "backend_error", status, message, detail }` — backend returned a `{error, detail, status_code}` envelope
   - `{ kind: "network", message }` — no response (DNS failure, offline, CORS preflight rejected)
   - `{ kind: "timeout", message }` — request cancelled by the client after `VITE_API_REQUEST_TIMEOUT_MS` (default 30s)
   - `{ kind: "cancelled", message }` — user-initiated cancellation via `AbortController`
5. **Persistence schema version (FR-029)**: The settings store persists `{ version: 1, selectedModel, topK, scoreThreshold, temperature, theme }`. On hydrate, if `version` is missing or higher than the supported version, the store falls back to defaults and logs a one-time warning via `lib/logger.ts`.

### Key technical decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Build tool | Vite 5 | Fast HMR, native ESM, zero-config TS, matches source plan doc |
| Framework | React 18 | Concurrent features, largest ecosystem, matches source plan doc |
| Type system | TypeScript 5 strict + `noUncheckedIndexedAccess` | FR-007 forbids `any`; `noUncheckedIndexedAccess` catches off-by-one array access that would otherwise only fail at runtime |
| Styling | Tailwind CSS 3 + shadcn/ui primitives | Utility-first, no runtime CSS-in-JS overhead (helps SC-004 Lighthouse), `shadcn/ui` gives accessible Radix-based components we own rather than vendor (see Rejected Alternatives) |
| Component primitives | shadcn/ui (Radix + cva + tailwind-merge) | Accessible-by-default primitives with full source control. Rejected MUI (runtime CSS + heavier bundle) and Chakra (runtime emotion) as they push us over the bundle budget |
| State management | Zustand 4 | Minimal API, TS-native, no context re-render cascades. Rejected Redux Toolkit (too much boilerplate for 3 stores), Context + useReducer (re-render hell), Jotai (atom model is overkill for 3 coarse slices) |
| Persistence | Zustand `persist` middleware → `localStorage` | Built-in, typed, supports partializing (only settings persist, not chat). Schema-version fallback satisfies FR-029 |
| HTTP client | Axios 1 | Interceptors for error normalisation and cancellation; `AbortController` support. Rejected `fetch` as primary because the boilerplate for timeout + error envelope + retry would reinvent Axios |
| Routing | React Router 6 (`createBrowserRouter`) | Data router API supports route-level code splitting and future loaders; matches source plan doc |
| Mock server | MSW 2 (service-worker mode in browser, node mode in tests) | Intercepts at the network layer so the API client is exercised in tests with no code-path difference. Rejected hand-rolled adapter swaps as they untype the API client |
| Unit/component tests | Vitest + React Testing Library | Vite-native (no separate Jest config), RTL is the user-event testing standard |
| Accessibility tests | `@axe-core/react` in component tests | Automates the SC-009 "zero critical a11y violations" gate; cheap to run in CI |
| E2E wiring | Playwright 1 installed + configured, no specs | Source plan doc assigns e2e specs to Feature 007; wiring the config here prevents divergence later |
| Logging | Hand-rolled `logger.ts` wrapping `console.*` with a JSON-like context object | Article IX "structured logging" intent without pulling in a client-side structlog dependency; ~30 lines of code |
| Bundle guardrails | `rollup-plugin-visualizer` on `npm run build:analyze` + CI budget check on gzipped JS | Makes the 200 KB budget observable rather than aspirational |
| Dev server port | 5173 (Vite default) | Matches Vite conventions; documented in `.env.example` and added to the backend CORS allowlist addendum |

### Rejected alternatives (worth recording)

- **Next.js** — rejected. SSR/SSG and route-handlers add surface area we don't need (the backend already exists as a FastAPI service), and the bundle overhead would put us at risk on SC-004. A pure SPA served as static files is the simpler, smaller option.
- **Vue / Svelte / SolidJS** — all viable, all rejected because the source plan doc explicitly calls for React; switching frameworks is not in scope.
- **Tanstack Query** for server state — deferred. It is the right tool once chat, conversation loading, and analytics fetching exist (Feature 006+); in this foundation feature, only the health check is fetched, and a hand-rolled hook is simpler than introducing a second state system alongside Zustand today. A follow-up note is captured in `research.md` so it is revisited at Feature 006.
- **Zod** for runtime validation of API responses — deferred. Compile-time TS interfaces are sufficient for the integration seam in this feature; adding runtime validation is a Feature 006+ concern once we have real response shapes to guard against (especially for streaming).
- **pnpm workspaces** / monorepo tooling — rejected. One frontend + one backend does not justify a workspace manager.
- **Storybook** — deferred to Feature 006 when there are enough user-visible components to browse.

### New dependencies (frontend only)

| Package | Version | Purpose |
|---------|---------|---------|
| react, react-dom | ^18.3 | UI framework |
| react-router-dom | ^6.26 | Client-side routing |
| zustand | ^4.5 | Global state + persist middleware |
| axios | ^1.7 | HTTP client |
| tailwindcss, autoprefixer, postcss | ^3.4 / latest / latest | Styling |
| @radix-ui/react-* (dialog, slot, etc.) | ^1.x | Accessible primitives used by shadcn/ui |
| class-variance-authority | ^0.7 | Variant-safe className helpers |
| tailwind-merge | ^2.4 | Dedup Tailwind classes |
| lucide-react | ^0.400 | Icon set |
| msw | ^2.4 | Mocked network layer |
| vite, @vitejs/plugin-react | ^5 / ^4 | Build tool |
| typescript | ^5.4 | Types |
| eslint + @typescript-eslint, eslint-plugin-react, eslint-plugin-react-hooks, eslint-plugin-jsx-a11y | latest | Linting |
| prettier | ^3 | Formatting |
| vitest, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, jsdom | ^1 / ^16 / latest / latest / latest | Unit + component tests |
| @axe-core/react | ^4 | Automated a11y tests |
| @playwright/test | ^1 | E2E wiring (specs in Feature 007) |
| rollup-plugin-visualizer | ^5 | Bundle analysis |

**No backend dependencies added.** Backend addenda listed above are config/schema changes handled under Feature 004, not here.

### Frontend config (`frontend/.env.example`)

```bash
# Backend base URL — required when VITE_ENABLE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000

# If "true", MSW intercepts all backend calls in-browser; the bundled app will
# still ship without MSW when built with VITE_ENABLE_MOCK=false.
VITE_ENABLE_MOCK=true

# Default LLM model identifier surfaced to the user (stored until they change it)
VITE_DEFAULT_MODEL=llama-3-8b-instant

# Reserved for Feature 006 streaming work; read but unused in this feature.
VITE_ENABLE_STREAMING=false

# Client-side request timeout in milliseconds (FR-023)
VITE_API_REQUEST_TIMEOUT_MS=30000
```

## Phase 0 Outputs (research.md)

See `research.md` for resolved technical unknowns:

- **R1**: React SPA build tool — Vite vs. Create React App vs. Next.js
- **R2**: State management — Zustand vs. Redux Toolkit vs. Context
- **R3**: Styling — Tailwind + shadcn/ui vs. MUI vs. Chakra vs. CSS Modules
- **R4**: HTTP client — Axios vs. native `fetch` + wrapper
- **R5**: Mocking strategy — MSW vs. stubbed Axios adapter vs. separate mock backend
- **R6**: Accessibility automation — `@axe-core/react` in component tests vs. dedicated Playwright a11y suite
- **R7**: Persistence — Zustand `persist` middleware vs. hand-rolled `localStorage` wrapper
- **R8**: Server-state caching — Tanstack Query now vs. deferred to Feature 006
- **R9**: TypeScript strictness settings that align with FR-007
- **R10**: Bundle-budget enforcement strategy

## Phase 1 Outputs

- `data-model.md` — Frontend-side entity schemas (ChatMessage, Conversation, User Preference Set, ApiResult, ApiError variants, Env Config) and their TS interfaces
- `contracts/api_client.md` — Typed endpoint signatures, request/response shapes, error envelope, mock-mode semantics, and the three pending-backend addenda
- `contracts/state_stores.md` — Zustand store public shapes (state + actions) and invariants
- `contracts/mock_server.md` — MSW handler inventory and sample-data shapes
- `quickstart.md` — Clone → install → dev-server → mock mode → tests → production build

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. This section intentionally left empty.
