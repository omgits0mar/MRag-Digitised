# Phase 0 Research: Frontend Foundation & Dev Environment

**Branch**: `005-frontend-foundation` | **Date**: 2026-04-12 | **Plan**: `plan.md`

This document resolves the technical unknowns raised in `plan.md` and records the rejected alternatives so future readers can follow the reasoning without retracing every comparison.

---

## R1 — React SPA build tool

**Decision**: Vite 5 with `@vitejs/plugin-react`.

**Rationale**: Vite's dev server is backed by native ESM and esbuild, giving sub-second cold start and near-instant HMR — both directly feed SC-001 (fresh clone to running dev in < 5 minutes) and the broader developer-productivity goal (US 5). The production build uses Rollup, which produces well-tree-shaken chunks and plays nicely with React Router's lazy imports, helping us stay under the 200 KB gzipped shell budget called out in `plan.md`. Vite also integrates natively with Vitest, eliminating a second test-runner config.

**Alternatives considered**:

- **Create React App** — effectively deprecated (no longer actively maintained), Webpack-based with slow cold starts. Rejected.
- **Next.js 14 (App Router)** — excellent framework, but SSR/server-components and route handlers overlap with the FastAPI backend and add bundle weight we don't need. Rejected as overkill for a SPA consuming an existing API.
- **Parcel** — zero-config is nice, but the React + Tailwind + TypeScript ecosystem is better documented for Vite, and Vite has clearer path-aliasing and env-var semantics.
- **Webpack 5 (hand-rolled)** — rejected on maintenance cost.

---

## R2 — State management

**Decision**: Zustand 4 with the `persist` middleware for the settings slice.

**Rationale**: We have exactly three coarse-grained state slices (chat, conversation, settings). Zustand gives typed selectors, no Provider, no context re-render cascades, and a ~1 KB gzipped footprint. The `persist` middleware handles `localStorage` round-tripping with a `version` field, which cleanly implements FR-028/FR-029 (persistence + corrupt-value fallback) without us writing our own migration machinery.

**Alternatives considered**:

- **Redux Toolkit** — the modern RTK API is fine, but for three slices the boilerplate (slices + reducers + middleware + Provider) is disproportionate. Rejected.
- **React Context + useReducer** — cheapest dependency-wise, but context re-renders every subscriber whenever any field changes; we'd have to split the settings into multiple contexts to avoid prop-drilling masquerading as context-drilling. FR-030 (subscribing without prop passage) is cleaner with a store.
- **Jotai / Recoil** — atom-based models are good for dense, overlapping derived state. Our state is three independent coarse slices; atoms would over-decompose.
- **MobX** — imperative mutation model fights React 18 concurrent rendering.

---

## R3 — Styling and component primitives

**Decision**: Tailwind CSS 3 + `shadcn/ui` primitives (Radix UI under the hood, wrapped with `class-variance-authority` and `tailwind-merge`; icons from `lucide-react`).

**Rationale**: Tailwind is utility-first with no runtime CSS-in-JS cost, which protects the SC-004 Lighthouse budget. `shadcn/ui` is not a dependency but a copy-into-source pattern — we own the components, so we can audit accessibility, restyle freely, and avoid vendor upgrade churn. Radix primitives underneath give us keyboard navigation and ARIA semantics (FR-034, FR-035) without reinventing them. `tailwind-merge` prevents the "last-className-wins" foot-gun when composing utilities across variants.

**Alternatives considered**:

- **MUI (Material UI)** — runtime emotion-based CSS, heavier bundle, and the Material design language conflicts with the product's brand neutrality. Rejected on bundle weight and aesthetic fit.
- **Chakra UI** — similar runtime CSS cost; ergonomics are nice, but we'd still need Radix for some primitives MSW doesn't ship well (e.g. headless combobox).
- **CSS Modules + hand-rolled components** — lots of rework to get a11y right; we'd be reimplementing Radix.
- **Stitches / vanilla-extract** — compile-time CSS-in-JS is great, but Tailwind is more widely known by the team and has a larger ecosystem of shadcn/ui-style kits.

---

## R4 — HTTP client

**Decision**: Axios 1 as the single HTTP client, wrapped in one module (`src/api/client.ts`) with request and response interceptors.

**Rationale**: Axios interceptors give us one place to implement error normalisation (FR-021), timeout (FR-023), cancellation via `AbortController` (FR-022), and the distinction between backend-error and network-unreachable (FR-024). Building the same surface over `fetch` is possible but reinvents Axios for negligible gain. The bundle cost (~14 KB minified, ~5 KB gzipped) is inside the 200 KB shell budget.

**Alternatives considered**:

- **Native `fetch` + thin wrapper** — viable, but the timeout + cancellation + retry + error-envelope wrapper quickly grows to "home-rolled Axios". Rejected.
- **Ky** — small and fetch-based; good option, but the ecosystem is smaller and several team members already know Axios's interceptor semantics.
- **Wretch** — similar to Ky; same verdict.

---

## R5 — Mocking strategy

**Decision**: MSW 2 in service-worker mode for the browser dev server, and MSW in node mode for tests.

**Rationale**: MSW intercepts at the network layer, which means the API client is exercised in tests with **zero code-path difference** between mock and real mode. This satisfies FR-031/FR-032 (mock mode covers every endpoint) without branching the API client implementation. Tests that stub at the function boundary (e.g. mocking `endpoints.ts`) would miss bugs in the client itself. MSW is removed from production bundles at build time (FR-033).

**Alternatives considered**:

- **Axios adapter swap** — replacing Axios's transport with a stub works, but we'd lose coverage of the interceptor chain in tests. Rejected.
- **json-server / separate mock backend** — another process to manage, and the mock lives outside the repo's test harness. Rejected on operational cost.
- **Sinon + fetch-mock** — older patterns, more setup for less coverage. Rejected.

---

## R6 — Accessibility automation

**Decision**: `@axe-core/react` assertions inside the Vitest component tests; Playwright-based a11y audits deferred to Feature 007.

**Rationale**: SC-009 calls for "zero critical a11y violations on the empty shell". `@axe-core/react` runs inside the jsdom component test environment and gives us the gate cheaply on every CI run. A dedicated Playwright a11y suite adds more coverage for rendered pixels (contrast, focus rings in real browsers) but is Feature 007 scope per the source plan doc; wiring Playwright here (config + directory) keeps the surface ready without adding specs.

**Alternatives considered**:

- **pa11y** — standalone CLI, adds a third test runner. Rejected on tooling sprawl.
- **Lighthouse CI a11y checks** — useful for rendered-page audits, but runs against a live URL; we'd need a CI dance to serve the built app. Deferred until Feature 007's Playwright suite lands.

---

## R7 — Persistence for user preferences

**Decision**: Zustand `persist` middleware writing JSON to `localStorage` under a versioned key (`mrag:settings:v1`), with a hand-written migration/fallback function that returns defaults if parsing fails or `version` is unrecognised.

**Rationale**: The middleware is built for exactly this use case, avoids reinventing `localStorage` serialisation, and supports `partialize` so only the settings slice is persisted (chat state is explicitly in-memory). The schema-version key makes FR-029 (corrupt-or-old data → defaults) a trivial guard.

**Alternatives considered**:

- **Hand-rolled `localStorage` wrapper** — 30 lines of code replicating the middleware without the partialize and migration hooks. Rejected.
- **IndexedDB (via idb-keyval)** — overkill for ~200 bytes of settings; adds async boot sequencing we don't need.
- **Cookies** — sent on every request, wrong tool for client-only state. Rejected.

---

## R8 — Server-state caching (Tanstack Query) — defer or adopt now?

**Decision**: Defer to Feature 006 (Chat UI Core).

**Rationale**: This foundation feature has exactly one server-state fetch (`GET /health`) powering the header badge. Introducing Tanstack Query for one endpoint adds a second state system (beyond Zustand) and ~12 KB gzipped — neither is justified today. A one-file `useHealthCheck` hook covers the need. Feature 006 will introduce multi-fetch flows (conversation list, conversation detail, streaming question) where Tanstack Query's dedup, retry, and cache-invalidation semantics genuinely pay off; this research note is the pointer back to this decision when Feature 006 is planned.

**Alternatives considered**:

- **Adopt Tanstack Query now** — rejected as premature; it would not be used for anything except the health check.
- **SWR** — similar trade-off.

---

## R9 — TypeScript strictness

**Decision**: `tsconfig.json` compiler options:

```json
{
  "strict": true,
  "noUncheckedIndexedAccess": true,
  "noFallthroughCasesInSwitch": true,
  "noImplicitOverride": true,
  "exactOptionalPropertyTypes": true,
  "useUnknownInCatchVariables": true,
  "forceConsistentCasingInFileNames": true,
  "skipLibCheck": true
}
```

**Rationale**: `strict: true` alone leaves several foot-guns wide open. `noUncheckedIndexedAccess` forces us to handle `undefined` on array/object index access — important for FR-007 (no `any`) because `any` is often smuggled in through untyped indexing. `exactOptionalPropertyTypes` catches the difference between "missing property" and "explicit undefined" which matters when we mirror backend Pydantic schemas. `useUnknownInCatchVariables` forces error-handling discipline in the Axios interceptor. `skipLibCheck` keeps build times reasonable.

**Alternatives considered**:

- **Only `strict: true`** — cheaper but leaks `any` through index access.
- **`noPropertyAccessFromIndexSignature`** — considered; rejected because it fights with idiomatic Zustand selectors.

---

## R10 — Bundle budget enforcement

**Decision**: `rollup-plugin-visualizer` on a dedicated `npm run build:analyze` script, plus a small CI check (shell script) that asserts the gzipped size of the main entry chunk is under 200 KB. No hard dependency on an external bundle-size service.

**Rationale**: Observability first, enforcement second. The visualizer gives a human a flamegraph when the budget is breached; the CI check stops regressions from landing without needing an external service. Keeping this local (rather than using `bundlesize` / `size-limit`) means the check runs in every environment that already runs tests.

**Alternatives considered**:

- **`size-limit`** — nice tool, but adds another config format and another dev dependency for a job a 10-line shell script can do.
- **No enforcement, only visualizer** — would let the budget drift; rejected because SC-004 is explicitly called out.

---

## Open follow-ups (for later features, not this one)

- **Tanstack Query adoption** — revisit in Feature 006 when multi-fetch flows exist (see R8).
- **Runtime response validation (zod)** — revisit in Feature 006 when streaming responses need per-token schema guards.
- **Storybook** — revisit in Feature 006 when the component library reaches ~10 user-visible components.
- **Dedicated Playwright a11y specs** — Feature 007 scope per source plan doc.
- **i18n of UI chrome** — out of scope for Phase 4 per source plan doc; revisit post-Phase 4.
