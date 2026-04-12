# Feature Specification: Frontend Foundation & Dev Environment

**Feature Branch**: `005-frontend-foundation`
**Created**: 2026-04-12
**Status**: Draft
**Input**: User description: "plan and build the specs for the new @docs/mrag-phase4-frontend-plan.md — kicks off Phase 4 (frontend) starting with the foundation feature: scaffold, API client layer, global state, and responsive application shell."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Responsive Application Shell for End Users (Priority: P1)

A user opens the MRAG web application in a browser and is presented with a coherent, responsive workspace: a persistent sidebar for navigation (Chat, History, Settings), a header identifying the product and exposing top-level controls, and a primary content area that hosts whichever view is currently active. The layout adapts fluidly from a mobile phone up to a large desktop monitor, with the sidebar collapsing into a hamburger-triggered drawer on narrow screens.

**Why this priority**: Without a navigable shell, no subsequent chat or settings features have a place to live. This is the minimum viewable surface a user can open in a browser and recognise as a working product, and it is the first thing a reviewer or stakeholder sees.

**Independent Test**: Open the app at any URL between 360px and 2560px wide, confirm the shell renders with sidebar + header + content region, and confirm the sidebar collapses into a hamburger menu at ≤768px and reopens as a drawer when toggled.

**Acceptance Scenarios**:

1. **Given** the app is loaded on a desktop viewport, **When** the user inspects the page, **Then** they see a sidebar with Chat / History / Settings navigation, a header with product branding, and an empty main content area with a welcome placeholder.
2. **Given** the app is loaded on a mobile viewport (≤768px), **When** the user inspects the page, **Then** the sidebar is hidden and a hamburger toggle is visible; **When** the user activates the toggle, **Then** the sidebar drawer slides in and navigation items are reachable.
3. **Given** the user is on the Chat view, **When** they click the History navigation item, **Then** the URL and content area update to the History view without a full-page reload.

---

### User Story 2 - Typed, Centralised Backend Integration (Priority: P1)

Every part of the frontend that needs data from the backend goes through a single, centralised integration layer with consistent error handling, environment-driven configuration, and a predictable shape for request and response data. When the backend is unavailable or returns an error, the layer surfaces a normalised, user-friendly error rather than a silent failure or raw stack trace.

**Why this priority**: Chat, conversation history, analytics, and evaluation features all depend on backend calls. Without a consistent integration layer the product will accumulate ad-hoc fetch calls that each handle errors, auth, and base URLs differently — which breaks down the moment the API contract changes.

**Independent Test**: With the backend reachable, a health check call through the integration layer returns a typed success payload; with the backend unreachable or returning a 5xx, the same call surfaces a normalised error containing a human-readable message and status code, and no raw exception reaches the UI.

**Acceptance Scenarios**:

1. **Given** the backend is running and healthy, **When** the shell requests the health status on load, **Then** a success indicator is shown and the typed response is available to other components.
2. **Given** the backend returns a 4xx error, **When** any component calls through the integration layer, **Then** the error is normalised into `{ message, status, detail }` and is surfaced in the UI rather than being swallowed.
3. **Given** the backend is unreachable, **When** a call is made, **Then** a "backend unreachable" error is surfaced with a suggested retry action, and no unhandled promise rejection is raised.
4. **Given** the backend base URL is configured via environment, **When** the environment changes between development, mock, and production targets, **Then** no source code changes are required to point the frontend at a different backend.

---

### User Story 3 - Shared Application State Without Prop Drilling (Priority: P1)

Chat messages, the list of past conversations, and user preferences (selected model, retrieval parameters, theme) are available to any component that needs to read or update them, without threading props through intermediate components. User preferences persist across page reloads so a returning user keeps the same model, parameters, and theme they last used.

**Why this priority**: Chat, history, and settings features are intrinsically cross-cutting — the header shows the selected model, the chat view uses it, and the settings view changes it. A shared state foundation must exist before any of those features are built.

**Independent Test**: Update a preference (e.g., selected model) from the settings view, observe the header and any other subscribed component reflect the change immediately, reload the browser, and confirm the preference is still in effect. Dispatch a state change from one component and verify a different component renders the new value.

**Acceptance Scenarios**:

1. **Given** two components subscribed to the same preference, **When** one component updates the preference, **Then** the other component re-renders with the new value without an explicit prop being passed between them.
2. **Given** a user has set preferences (selected model, top-k, score threshold, temperature, theme), **When** the page is reloaded, **Then** those preferences are restored to their previous values.
3. **Given** application state (chat messages, active conversation, streaming flag), **When** the user navigates between views, **Then** the in-memory state is preserved for the lifetime of the session.

---

### User Story 4 - Frontend Can Be Developed and Demoed Without a Live Backend (Priority: P2)

A developer or reviewer who does not have the backend running can still start the frontend, explore all views, and exercise the primary flows against realistic sample data. A toggle (environment variable or setting) switches between real backend calls and the mocked responses.

**Why this priority**: Reviewers evaluating the project, frontend-only contributors, and offline demos all benefit from being able to run the UI in isolation. It also removes a common source of flaky tests (tests that silently depend on a running backend).

**Independent Test**: With the backend not running, start the frontend in mock mode, navigate every top-level view, and confirm that each view renders with plausible sample data rather than error states.

**Acceptance Scenarios**:

1. **Given** mock mode is enabled and the backend is not running, **When** the user opens the app, **Then** every view renders with realistic placeholder data and no network errors surface.
2. **Given** mock mode is disabled, **When** the user opens the app, **Then** data is fetched from the configured backend and mock responses are not used.

---

### User Story 5 - Developer Productivity Baseline (Priority: P2)

A developer who has cloned the repository for the first time can install dependencies, start the dev server with hot-reload, run the test suite, and run the linter with a small, documented set of commands. A production build produces optimised static assets with zero errors and zero type-checker warnings.

**Why this priority**: Nothing else in Phase 4 can proceed without a reliable local loop. If the scaffold is flaky, every subsequent feature inherits the flakiness. It is P2 rather than P1 because end users do not directly experience it, but it is blocking for downstream work.

**Independent Test**: On a clean checkout, a single documented command installs dependencies, a second documented command starts the dev server with hot-reload working, a third runs the test suite to completion, and a fourth produces a production build with zero errors.

**Acceptance Scenarios**:

1. **Given** a fresh clone of the repository, **When** the documented setup command is run, **Then** all dependencies install successfully.
2. **Given** installed dependencies, **When** the dev command is run, **Then** the app becomes available on a local URL and edits to source files trigger a hot reload within a few seconds.
3. **Given** installed dependencies, **When** the build command is run, **Then** it exits with zero errors and zero type warnings and produces bundled static assets.
4. **Given** installed dependencies, **When** the lint command is run, **Then** the codebase passes with zero violations.

---

### Edge Cases

- **Backend schema drift**: Backend response shape changes between versions. The integration layer must fail loudly at a single location rather than causing runtime errors in many components.
- **Slow or hung backend**: A request that never resolves must be cancellable and must not leave the UI stuck in a loading state forever — a user-visible timeout message and retry are required.
- **Missing or malformed environment configuration**: If a required environment variable is absent on startup, the app must surface a clear, actionable error (e.g., "API base URL is not configured") instead of making requests to an undefined host.
- **Viewport extremes**: At ≤360px (smallest supported mobile width), all primary navigation must remain reachable; at ultra-wide desktop widths, content must not become awkwardly stretched.
- **Partial state persistence**: If persisted preferences are corrupted or written by an older app version, the app must fall back to defaults rather than failing to load.
- **Concurrent state updates**: Multiple components writing to the same state slice within the same tick must not produce lost updates or inconsistent renders.

## Requirements *(mandatory)*

### Functional Requirements

**Project scaffold & developer experience**

- **FR-001**: The frontend MUST live in a dedicated `frontend/` directory at the repository root, isolated from the backend source tree.
- **FR-002**: A documented, single command MUST install all frontend dependencies on a clean checkout.
- **FR-003**: A documented, single command MUST start a local development server with hot module replacement.
- **FR-004**: A documented, single command MUST produce an optimised production build; the build MUST exit non-zero on any type error or compilation error.
- **FR-005**: A documented, single command MUST run the full frontend unit test suite and report pass/fail.
- **FR-006**: A documented, single command MUST run the frontend linter/formatter and report violations; the baseline codebase MUST pass with zero violations.
- **FR-007**: Source code MUST be type-checked under strict settings; explicit "any" types MUST NOT be used in the baseline scaffold.

**Configuration & environment**

- **FR-008**: The backend base URL, mock-mode toggle, default model, and streaming-enabled flag MUST be configurable via environment variables; no hard-coded hostnames or secrets in source.
- **FR-009**: An `.env.example` file MUST document every environment variable the frontend consumes.
- **FR-010**: If a required environment variable is missing at startup, the app MUST surface a visible, actionable error.

**Application shell**

- **FR-011**: The app MUST render a persistent sidebar with navigation entries for Chat, History, and Settings.
- **FR-012**: The app MUST render a header containing product identity and space for global controls (e.g., model selector in later features).
- **FR-013**: The app MUST render a primary content region that displays the active view.
- **FR-014**: Navigation between Chat, History, and Settings MUST NOT cause a full-page reload and MUST update the URL so that the current view is reflected and deep-linkable.
- **FR-015**: The layout MUST render correctly across viewport widths from 360px to 2560px.
- **FR-016**: At viewport widths ≤768px, the sidebar MUST collapse and be reachable via a hamburger toggle; activating the toggle MUST reveal/hide the sidebar as a drawer.
- **FR-017**: The current active navigation entry MUST be visually distinguished from inactive entries.

**Backend integration layer**

- **FR-018**: All backend calls MUST go through a single, centralised integration layer; components MUST NOT make direct network calls.
- **FR-019**: The integration layer MUST expose typed functions for every backend endpoint consumed by the frontend (health, ask question, list conversations, get conversation, delete conversation, analytics, evaluation).
- **FR-020**: Request and response shapes exposed by the integration layer MUST match the backend API contract exactly, so that a backend schema change causes a single, compile-time failure rather than silent runtime errors.
- **FR-021**: The integration layer MUST normalise errors into a consistent shape containing at minimum: human-readable message, status code, and optional detail.
- **FR-022**: The integration layer MUST support cancelling in-flight requests (e.g., when the user navigates away or starts a new query).
- **FR-023**: The integration layer MUST apply a user-visible timeout to requests so that no request can hang indefinitely.
- **FR-024**: The integration layer MUST surface network-unreachable failures distinctly from backend-returned errors so the UI can offer appropriate recovery actions.

**Shared application state**

- **FR-025**: The frontend MUST provide a shared state facility for chat state (messages, streaming flag, active conversation, last error).
- **FR-026**: The frontend MUST provide a shared state facility for conversation history (list, active id, load/delete actions).
- **FR-027**: The frontend MUST provide a shared state facility for user preferences (selected model, top-k, score threshold, temperature, theme).
- **FR-028**: User preferences MUST persist across browser reloads via local storage.
- **FR-029**: Persisted preferences that fail to deserialize (corrupt or from an incompatible version) MUST fall back to documented defaults without blocking app startup.
- **FR-030**: Any component MUST be able to subscribe to a state slice without receiving it as a prop from an ancestor.

**Mock mode for backend-independent development**

- **FR-031**: The frontend MUST support a mock mode, toggleable via environment variable, in which every backend endpoint returns realistic sample data without requiring a running backend.
- **FR-032**: Mock responses MUST cover every endpoint the frontend calls, so that every view can be exercised in mock mode.
- **FR-033**: The mock layer MUST NOT be bundled into the production build.

**Accessibility & quality baseline**

- **FR-034**: Primary navigation and interactive elements MUST be reachable via keyboard alone.
- **FR-035**: Interactive elements MUST have accessible labels suitable for screen readers.
- **FR-036**: Colour choices in both default and dark variants MUST meet WCAG AA contrast for body text and interactive controls.

### Key Entities *(include if feature involves data)*

- **Application User**: The person using the frontend in the browser. Has preferences that persist across sessions. Does not require authentication in this feature.
- **Application View**: A top-level destination in the shell (Chat, History, Settings). Deep-linkable via URL; exactly one is active at a time.
- **User Preference Set**: Selected model, retrieval parameters (top-k, score threshold, temperature), theme, and any other user-tunable options. Persisted locally to the user's browser.
- **Backend Request**: A typed call from the frontend to the backend, with a known input shape, output shape, normalised error shape, and cancellation handle.
- **Backend Error**: A normalised representation of any failure from the backend layer, distinguishing network-unreachable errors from errors returned by the backend.
- **Mock Response Set**: A bundle of realistic sample payloads keyed by endpoint, used when mock mode is enabled.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new developer can go from a fresh clone to a running dev server in under 5 minutes following only the documented commands.
- **SC-002**: The production build exits with zero errors, zero type-check warnings, and zero lint violations.
- **SC-003**: The application shell renders correctly (no horizontal scroll, all primary navigation reachable) at every viewport width from 360px to 2560px in supported modern browsers.
- **SC-004**: A first-paint measurement on an empty shell completes in under 3 seconds on a mid-range laptop over a typical home broadband connection, and the Lighthouse performance score on the empty shell is at least 85.
- **SC-005**: 100% of backend calls made by the frontend go through the centralised integration layer (verified by a repository-wide check that no component imports a raw HTTP client directly).
- **SC-006**: Every user-visible failure path (4xx, 5xx, unreachable, timeout) results in a human-readable message rather than a blank screen, unhandled promise rejection, or raw stack trace.
- **SC-007**: A user who sets preferences, reloads the browser, and reopens the app sees the same preferences restored 100% of the time (excluding cases of deliberate storage clear).
- **SC-008**: With mock mode enabled and the backend not running, every top-level view in the shell renders without any "failed to fetch" errors.
- **SC-009**: Primary shell functions (navigating between views, toggling the mobile sidebar) are fully operable via keyboard, and automated accessibility checks on the empty shell report zero critical violations.
- **SC-010**: A backwards-incompatible change in a backend response shape surfaces at build time in exactly one location (the integration layer) rather than as runtime errors in multiple components.

## Assumptions

- Phase 3 backend (Features 003 and 004 in this repository — FastAPI app and database integration) is available as the integration target; where Phase 3 endpoints are incomplete or need extension for the frontend (e.g., streaming, a models listing, CORS for the frontend origin), those are tracked as backend addenda tasks separate from this feature.
- A modern evergreen browser (latest two versions of Chrome, Firefox, Safari, Edge) is the target runtime; IE11 and other legacy browsers are out of scope.
- Node.js (LTS) and npm are available on all developer machines; Node version requirements will be pinned in the project's package manifest.
- No end-user authentication or multi-user session management is required in this feature — a single implicit user is assumed. Auth may be layered in later without restructuring the shell.
- User preferences are stored in the browser only; no server-side user profile is synced in this feature.
- Offline support beyond mock mode (service workers, offline caching of real data) is out of scope.
- Internationalisation of UI chrome is out of scope for this feature; the MRAG retrieval stack itself is multilingual per the project constitution, but the shell's static strings are English-only in this feature.
- Telemetry / analytics of frontend usage (as distinct from the backend analytics dashboard built in a later feature) is out of scope here.
- The shell provides placeholder content for Chat, History, and Settings views; the fully functional versions of those views are delivered by follow-on features (Chat UI Core and Advanced Chat Features).
