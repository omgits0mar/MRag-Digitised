# Frontend Workspace

The frontend lives in [`frontend/`](.) as a Vite + React + TypeScript application that talks to
the MRAG FastAPI backend through the typed API layer in `src/api/`.

## Environment

Use the repository's `mrag` conda environment for all frontend commands. Node and npm are expected
to come from that environment.

```bash
conda activate mrag
cd frontend
```

You can also run commands from the repository root with `conda run -n mrag ...` if you prefer not
to activate the environment interactively.

## Install

```bash
conda activate mrag
cd frontend
cp .env.example .env
npm install
```

## Daily workflow

```bash
npm run dev
npm run test
npm run lint
npm run typecheck
```

Mock mode is controlled by `VITE_ENABLE_MOCK` in `.env`. With the default `true` value, the app
boots against MSW and does not require the backend to be running.

## Build and preview

```bash
npm run build
npm run build:check
npm run preview
```

`build:check` enforces the frontend bundle budget and confirms production output does not retain
MSW artifacts. The build scripts force `VITE_ENABLE_MOCK=false` so production output is always
generated without mock-mode code paths.

## Additional scripts

```bash
npm run build:analyze
npm run test:e2e
```

- `build:analyze` writes `dist/stats.html` using the Rollup visualizer.
- `test:e2e` is scaffolded for downstream Playwright specs.

## File map

- `src/components/layout/`: shell, header, sidebar, theme provider, env banner
- `src/stores/`: Zustand stores for chat, conversations, and persisted settings
- `src/api/`: typed backend DTOs, Axios client, endpoint wrappers
- `src/mocks/`: MSW browser worker, handlers, and sample payloads
- `tests/`: Vitest unit and integration coverage
