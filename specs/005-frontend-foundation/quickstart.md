# Quickstart: Frontend Foundation

**Branch**: `005-frontend-foundation` | **Plan**: `plan.md`

This quickstart verifies the acceptance criteria for a completed Feature 005: fresh clone → running dev server → mock mode exercised → tests green → production build clean. The steps are written so a new contributor can follow them without having read the spec.

---

## 0. Prerequisites

- The `mrag` conda environment is available locally and includes the Node/npm toolchain used by this repo.
- A POSIX shell (bash / zsh). Commands are from the repository root.

Activate the environment before running any frontend commands:

```bash
conda activate mrag
```

---

## 1. Install frontend dependencies

```bash
cd frontend
cp .env.example .env   # first time only
npm install
```

Expected: dependencies resolve without peer-dependency warnings that block install; `node_modules/` populates.

---

## 2. Start the dev server (mock mode — no backend needed)

With `.env` containing `VITE_ENABLE_MOCK=true` (the default from `.env.example`):

```bash
npm run dev
```

Expected:

- Dev server starts on `http://localhost:5173`.
- Console shows `[MSW] Mocking enabled` once.
- Opening the URL renders the shell: Sidebar (Chat / History / Settings), Header with product name, and a welcome placeholder in the main content area.
- Clicking each sidebar entry navigates without a full reload; the URL updates to `/`, `/history`, `/settings`.
- Resizing the browser below 768px collapses the sidebar into a hamburger drawer.

Verifies: US 1 (shell), US 3 (state) via theme toggle persistence, US 4 (mock mode).

---

## 3. Start the dev server against the real backend

```bash
# In a second terminal, start the backend:
conda activate mrag
uvicorn src.mrag.api.app:app --reload --port 8000
```

Then edit `frontend/.env`:

```bash
VITE_ENABLE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000
```

Restart the dev server. The Header health indicator should switch from "mocked" to "ok" within a few seconds.

**Backend addendum needed**: the backend must have `http://localhost:5173` in `Settings.api_cors_origins` or the preflight will be rejected and the client will surface `{ kind: "network", message: "Backend is unreachable" }`. If the addendum has not landed yet, stay on mock mode for now.

Verifies: FR-018 (single integration seam), FR-021 (error normalisation), FR-024 (network vs backend error distinction).

---

## 4. Run unit + component + integration tests

```bash
cd frontend
npm run test
```

Expected:

- Vitest runs to completion with 0 failures.
- Coverage summary is printed (coverage thresholds NOT enforced in this feature — Feature 007 will add them).
- `@axe-core/react` assertions pass for the empty shell (zero critical violations).

Useful variants:

```bash
npm run test:watch        # watch mode during development
npm run typecheck         # tsc --noEmit only
npm run lint              # ESLint across src/ and tests/
npm run format            # Prettier write
npm run test:e2e          # Playwright scaffold for downstream specs
```

Verifies: SC-002 (zero errors/warnings/lint), SC-009 (a11y baseline).

---

## 5. Produce a production build

```bash
cd frontend
npm run build
npm run build:check        # post-build isolation + bundle-budget checks
npm run build:analyze      # optional Rollup visualizer output
```

Expected:

- `npm run build` exits 0, produces `dist/` with an `index.html` plus hashed JS/CSS chunks.
- `npm run build:check`:
  - Fails if `dist/` contains any reference to `mockServiceWorker`, `from "msw"`, or `@mswjs` (FR-033).
  - Fails if the main entry chunk exceeds 200 KB gzipped.
  - Prints the gzipped size of each chunk for review.
- `npm run build:analyze` writes `dist/stats.html` for chunk inspection.

Preview the production bundle locally:

```bash
npm run preview            # serves dist/ on :4173
```

Verifies: SC-002 (clean build), FR-033 (mocks not in prod), the 200 KB shell-bundle budget.

---

## 6. Lighthouse + a11y spot-check

With the preview server running:

```bash
npx lighthouse http://localhost:4173 \
  --only-categories=performance,accessibility \
  --output=json --output-path=./lighthouse.json \
  --chrome-flags="--headless"
```

Expected:

- `performance` ≥ 85 (SC-004).
- `accessibility` ≥ 95.
- LCP ≤ 3s on your machine (SC-004 sanity check; CI runs the authoritative check).

Verifies: SC-004 (performance), SC-009 (accessibility).

---

## 7. Acceptance walkthrough

Having completed steps 1–6 with no failures, the following user stories from `spec.md` have been exercised end-to-end:

| Story | Verified by |
|-------|-------------|
| US 1 (Shell) | Step 2 — shell renders, nav works, mobile collapse. |
| US 2 (API integration) | Step 3 — real backend call via integration layer; Step 4 — error normalisation tests. |
| US 3 (Shared state) | Step 4 — store tests cover persistence, subscription, defaults fallback. |
| US 4 (Mock mode) | Step 2 — all views render in mock mode; Step 5 — mocks absent from prod build. |
| US 5 (Dev productivity) | Steps 1, 4, 5 — single-command install, test, build. |

---

## Troubleshooting

- **`npm run dev` fails with `ENV_NOT_CONFIGURED`**: `.env` is missing or `VITE_DEFAULT_MODEL` is unset. Copy `.env.example` to `.env`.
- **Mock mode appears enabled but API calls go to the real URL**: hard-refresh the browser (Ctrl/Cmd+Shift+R). The MSW service worker caches its registration.
- **`npm run build:check` fails on bundle budget**: run `npm run build:analyze`, open the generated `stats.html`, and look for unexpected deps (typical culprits: importing the whole `lucide-react` set instead of specific icons).
- **`@axe-core/react` reports "Document does not have a main landmark"**: every page component (even placeholder) must render inside a `<main>` element. Placeholders in this feature do this; custom pages added later must maintain it.
