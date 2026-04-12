# Tasks: Frontend Foundation & Dev Environment

**Input**: Design documents from `/specs/005-frontend-foundation/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Included. The specification explicitly requires a frontend test suite, accessibility checks, and build/lint/typecheck validation.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (`US1`..`US5`)
- Every task includes exact file paths

## Path Conventions

- Frontend application code lives under `frontend/`
- Frontend tests live under `frontend/tests/`
- Backend addenda described in the contracts are intentionally out of scope for this feature's `tasks.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new frontend workspace and baseline toolchain files.

- [X] T001 Initialize the frontend workspace manifests in `frontend/package.json` and `frontend/.gitignore`
- [X] T002 [P] Add TypeScript and Vite project configuration in `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, and `frontend/vite.config.ts`
- [X] T003 [P] Configure Tailwind and PostCSS in `frontend/tailwind.config.ts`, `frontend/postcss.config.js`, and `frontend/src/styles/globals.css`
- [X] T004 [P] Configure linting and formatting in `frontend/.eslintrc.cjs` and `frontend/.prettierrc`
- [X] T005 Create the frontend environment and HTML entry assets in `frontend/.env.example`, `frontend/index.html`, and `frontend/public/favicon.svg`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the core runtime, shared utilities, and test harness that all stories depend on.

**⚠️ CRITICAL**: No user story work should start until this phase is complete.

- [X] T006 Create the app bootstrap and route entry points in `frontend/src/main.tsx`, `frontend/src/App.tsx`, and `frontend/src/router.tsx`
- [X] T007 [P] Implement typed environment loading and defaults in `frontend/src/config.ts` and `frontend/src/types/env.d.ts`
- [X] T008 [P] Add shared frontend utilities in `frontend/src/lib/logger.ts` and `frontend/src/lib/cn.ts`
- [X] T009 [P] Set up the frontend test harness in `frontend/tests/setup.ts` and `frontend/tests/e2e/README.md`
- [X] T010 [P] Enforce the single API seam and import aliases in `frontend/.eslintrc.cjs`, `frontend/tsconfig.json`, and `frontend/vite.config.ts`

**Checkpoint**: Frontend workspace, runtime bootstrap, and shared tooling are ready for story work.

---

## Phase 3: User Story 1 - Responsive Application Shell for End Users (Priority: P1) 🎯 MVP

**Goal**: Deliver a responsive routed shell with sidebar, header, mobile drawer behavior, and placeholder pages.

**Independent Test**: Open the app from 360px to 2560px, verify the shell renders with Chat / History / Settings navigation, and confirm the sidebar collapses into a hamburger-triggered drawer at ≤768px.

### Tests for User Story 1

- [X] T011 [P] [US1] Add responsive shell and accessibility coverage in `frontend/tests/integration/test_app_shell.tsx`
- [X] T012 [P] [US1] Add route navigation coverage in `frontend/tests/integration/test_routing.tsx`

### Implementation for User Story 1

- [X] T013 [P] [US1] Create routed placeholder pages in `frontend/src/pages/ChatPage.tsx`, `frontend/src/pages/HistoryPage.tsx`, and `frontend/src/pages/SettingsPage.tsx`
- [X] T014 [P] [US1] Implement primary navigation and the mobile drawer in `frontend/src/components/layout/Sidebar.tsx`
- [X] T015 [P] [US1] Implement the shell header and global-control slots in `frontend/src/components/layout/Header.tsx`
- [X] T016 [US1] Compose the responsive application shell in `frontend/src/components/layout/AppShell.tsx`
- [X] T017 [US1] Wire lazy-loaded routes, active-nav state, and deep-linkable navigation in `frontend/src/router.tsx` and `frontend/src/App.tsx`

**Checkpoint**: The frontend shell is navigable, responsive, and independently demoable.

---

## Phase 4: User Story 2 - Typed, Centralised Backend Integration (Priority: P1)

**Goal**: Create a single typed API layer with config-driven behavior, normalized errors, health checks, and visible startup failure handling.

**Independent Test**: With the backend reachable, a health call returns typed data through the integration layer; with the backend unreachable or returning errors, the UI receives a normalized, human-readable failure instead of a thrown exception.

### Tests for User Story 2

- [X] T018 [P] [US2] Add API client timeout, cancellation, and error-normalization tests in `frontend/tests/unit/api/test_client.ts`
- [X] T019 [P] [US2] Add endpoint request-shape and response-wrapping tests in `frontend/tests/unit/api/test_endpoints.ts`
- [X] T020 [P] [US2] Add missing-environment startup coverage in `frontend/tests/integration/test_env_banner.tsx`

### Implementation for User Story 2

- [X] T021 [P] [US2] Mirror backend DTOs and client error/result contracts in `frontend/src/api/types.ts`
- [X] T022 [US2] Implement the Axios singleton and request cancellation helper in `frontend/src/api/client.ts`
- [X] T023 [US2] Implement typed endpoint wrappers for health, ask-question, conversations, analytics, evaluation, and models in `frontend/src/api/endpoints.ts`
- [X] T024 [P] [US2] Implement the header health-check hook in `frontend/src/hooks/useHealthCheck.ts`
- [X] T025 [P] [US2] Implement visible startup configuration failure UI in `frontend/src/components/layout/EnvBanner.tsx`
- [X] T026 [US2] Connect config validation and health status rendering in `frontend/src/main.tsx` and `frontend/src/components/layout/Header.tsx`

**Checkpoint**: Every frontend network call can flow through one typed seam with consistent errors and observable health state.

---

## Phase 5: User Story 3 - Shared Application State Without Prop Drilling (Priority: P1)

**Goal**: Provide shared chat, conversation, and settings state with persisted preferences and theme synchronization.

**Independent Test**: Change a preference in Settings, verify Header or another subscriber updates immediately, reload the browser, and confirm the preference persists while in-memory session state remains stable across route changes.

### Tests for User Story 3

- [X] T027 [P] [US3] Add chat store state-transition coverage in `frontend/tests/unit/stores/test_chatStore.ts`
- [X] T028 [P] [US3] Add conversation store load-and-delete coverage in `frontend/tests/unit/stores/test_conversationStore.ts`
- [X] T029 [P] [US3] Add settings persistence and fallback coverage in `frontend/tests/unit/stores/test_settingsStore.ts`

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement session-scoped chat state in `frontend/src/stores/chatStore.ts`
- [X] T031 [P] [US3] Implement conversation list state and optimistic delete behavior in `frontend/src/stores/conversationStore.ts`
- [X] T032 [P] [US3] Implement persisted user preference state in `frontend/src/stores/settingsStore.ts`
- [X] T033 [P] [US3] Implement theme synchronization from persisted settings in `frontend/src/components/layout/ThemeProvider.tsx`
- [X] T034 [US3] Bind shared state selectors into `frontend/src/components/layout/Header.tsx`, `frontend/src/pages/HistoryPage.tsx`, and `frontend/src/pages/SettingsPage.tsx`

**Checkpoint**: Shared state is available without prop drilling, and persisted preferences survive reloads safely.

---

## Phase 6: User Story 4 - Frontend Can Be Developed and Demoed Without a Live Backend (Priority: P2)

**Goal**: Enable backend-independent development through MSW-backed mock mode with realistic sample payloads.

**Independent Test**: Start the app with the backend stopped and `VITE_ENABLE_MOCK=true`, then navigate each top-level view and confirm it renders without network failures while using realistic mock data.

### Tests for User Story 4

- [X] T035 [P] [US4] Add mock-mode integration coverage for all top-level views in `frontend/tests/integration/test_mock_mode.tsx`

### Implementation for User Story 4

- [X] T036 [P] [US4] Create typed sample backend payloads in `frontend/src/mocks/data.ts`
- [X] T037 [P] [US4] Implement MSW handlers and browser worker setup in `frontend/src/mocks/handlers.ts` and `frontend/src/mocks/browser.ts`
- [X] T038 [US4] Gate MSW startup before React renders in `frontend/src/main.tsx`

**Checkpoint**: The frontend can be run, reviewed, and tested without a live backend.

---

## Phase 7: User Story 5 - Developer Productivity Baseline (Priority: P2)

**Goal**: Make install, dev, lint, test, and production build flows predictable and documented for new contributors.

**Independent Test**: From a clean checkout, install dependencies, start the dev server with HMR, run the test suite, run lint/typecheck, and produce a production build with zero errors using the documented commands.

### Tests for User Story 5

- [X] T039 [P] [US5] Finalize exact frontend dependencies and npm scripts in `frontend/package.json` and `frontend/package-lock.json`

### Implementation for User Story 5

- [X] T040 [P] [US5] Add build analysis and bundle-budget enforcement in `frontend/scripts/build-check.mjs` and `frontend/vite.config.ts`
- [X] T041 [P] [US5] Configure Playwright scaffolding for downstream end-to-end work in `frontend/playwright.config.ts` and `frontend/tests/e2e/README.md`
- [X] T042 [US5] Document install, dev, lint, test, build, preview, and mock-mode workflows in `frontend/README.md`

**Checkpoint**: A new developer has a documented, repeatable local loop for the frontend workspace.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Close the quality gaps that span multiple stories and align repo-level docs with the new frontend workspace.

- [X] T043 [P] Add logger utility coverage in `frontend/tests/unit/lib/test_logger.ts`
- [X] T044 Tune accessible theme tokens and shell styling in `frontend/src/styles/globals.css` and `frontend/tailwind.config.ts`
- [X] T045 Update repo-level onboarding for the frontend workspace in `README.md`
- [X] T046 Run the feature acceptance walkthrough and record any command or expectation adjustments in `specs/005-frontend-foundation/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** has no dependencies and starts immediately.
- **Phase 2: Foundational** depends on Phase 1 and blocks all story work.
- **Phases 3-5: US1, US2, US3** depend on Phase 2 and can proceed in parallel after the foundation is complete.
- **Phase 6: US4** depends on the UI surfaces from US1 and the API layer from US2; it also benefits from the shared state from US3.
- **Phase 7: US5** depends on the workspace scaffold from Phases 1-2 and should be finalized after the core frontend flows are in place.
- **Phase 8: Polish** depends on the desired story phases being complete.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational; no dependency on other stories.
- **US2 (P1)**: Starts after Foundational; no dependency on other stories.
- **US3 (P1)**: Starts after Foundational; no dependency on other stories.
- **US4 (P2)**: Depends on US1 and US2, and integrates cleanly with US3.
- **US5 (P2)**: Depends on the frontend scaffold and should validate the completed developer workflow after US1-US4 land.

### Within Each User Story

- Write the listed tests first and verify they fail for the intended missing behavior.
- Implement models/types/state before wiring components or runtime integration.
- Complete the story’s integration task before moving to the next dependent story.
- Validate each story independently using its stated independent test.

---

## Parallel Opportunities

- **Setup**: T002-T004 can run in parallel after T001.
- **Foundational**: T007-T010 can run in parallel after T006 establishes the app entry structure.
- **US1**: T011-T015 can run in parallel; T016-T017 then compose the shell.
- **US2**: T018-T021, T024, and T025 can run in parallel before T022-T023-T026 integration.
- **US3**: T027-T033 can run in parallel, then T034 binds the state into the UI.
- **US4**: T035-T037 can run in parallel before T038 wires mock startup into boot.
- **US5**: T039-T041 can run in parallel before T042 documents the final workflow.
- **Polish**: T043-T045 can run in parallel, with T046 last as the acceptance pass.

---

## Parallel Example: User Story 1

```bash
Task: "T011 [US1] Add responsive shell and accessibility coverage in frontend/tests/integration/test_app_shell.tsx"
Task: "T012 [US1] Add route navigation coverage in frontend/tests/integration/test_routing.tsx"
Task: "T013 [US1] Create routed placeholder pages in frontend/src/pages/ChatPage.tsx, frontend/src/pages/HistoryPage.tsx, and frontend/src/pages/SettingsPage.tsx"
Task: "T014 [US1] Implement primary navigation and the mobile drawer in frontend/src/components/layout/Sidebar.tsx"
Task: "T015 [US1] Implement the shell header and global-control slots in frontend/src/components/layout/Header.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "T018 [US2] Add API client timeout, cancellation, and error-normalization tests in frontend/tests/unit/api/test_client.ts"
Task: "T019 [US2] Add endpoint request-shape and response-wrapping tests in frontend/tests/unit/api/test_endpoints.ts"
Task: "T020 [US2] Add missing-environment startup coverage in frontend/tests/integration/test_env_banner.tsx"
Task: "T021 [US2] Mirror backend DTOs and client error/result contracts in frontend/src/api/types.ts"
Task: "T024 [US2] Implement the header health-check hook in frontend/src/hooks/useHealthCheck.ts"
Task: "T025 [US2] Implement visible startup configuration failure UI in frontend/src/components/layout/EnvBanner.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "T027 [US3] Add chat store state-transition coverage in frontend/tests/unit/stores/test_chatStore.ts"
Task: "T028 [US3] Add conversation store load-and-delete coverage in frontend/tests/unit/stores/test_conversationStore.ts"
Task: "T029 [US3] Add settings persistence and fallback coverage in frontend/tests/unit/stores/test_settingsStore.ts"
Task: "T030 [US3] Implement session-scoped chat state in frontend/src/stores/chatStore.ts"
Task: "T031 [US3] Implement conversation list state and optimistic delete behavior in frontend/src/stores/conversationStore.ts"
Task: "T032 [US3] Implement persisted user preference state in frontend/src/stores/settingsStore.ts"
Task: "T033 [US3] Implement theme synchronization from persisted settings in frontend/src/components/layout/ThemeProvider.tsx"
```

## Parallel Example: User Story 4

```bash
Task: "T035 [US4] Add mock-mode integration coverage for all top-level views in frontend/tests/integration/test_mock_mode.tsx"
Task: "T036 [US4] Create typed sample backend payloads in frontend/src/mocks/data.ts"
Task: "T037 [US4] Implement MSW handlers and browser worker setup in frontend/src/mocks/handlers.ts and frontend/src/mocks/browser.ts"
```

## Parallel Example: User Story 5

```bash
Task: "T039 [US5] Finalize exact frontend dependencies and npm scripts in frontend/package.json and frontend/package-lock.json"
Task: "T040 [US5] Add build analysis and bundle-budget enforcement in frontend/scripts/build-check.mjs and frontend/vite.config.ts"
Task: "T041 [US5] Configure Playwright scaffolding for downstream end-to-end work in frontend/playwright.config.ts and frontend/tests/e2e/README.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate the responsive shell independently
5. Demo the frontend shell before expanding the runtime surface

### Incremental Delivery

1. Finish Setup + Foundational to establish the frontend workspace
2. Deliver US1 for the visible shell
3. Deliver US2 for the API seam and health status
4. Deliver US3 for shared state and persisted settings
5. Deliver US4 for backend-independent development
6. Deliver US5 for developer workflow hardening
7. Finish with Phase 8 polish and the quickstart acceptance sweep

### Parallel Team Strategy

1. One developer completes Setup + Foundational
2. After Phase 2:
   - Developer A: US1 shell
   - Developer B: US2 API layer
   - Developer C: US3 stores and theme state
3. After US1-US3 stabilize:
   - Developer A or B: US4 mock mode
   - Developer C: US5 developer workflow and docs
4. Finish together on Phase 8 polish and quickstart validation

---

## Notes

- Total tasks: 46
- User story task counts:
  - US1: 7 tasks
  - US2: 9 tasks
  - US3: 8 tasks
  - US4: 4 tasks
  - US5: 4 tasks
- Setup tasks: 5
- Foundational tasks: 5
- Polish tasks: 4
- All task lines follow the required checklist format: checkbox, task ID, optional `[P]`, required story label for story phases, and exact file paths
- Backend addenda from `contracts/api_client.md` are intentionally excluded because the plan marks them as follow-up work outside this feature
