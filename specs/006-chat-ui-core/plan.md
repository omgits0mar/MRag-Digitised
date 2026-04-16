# Implementation Plan: Chat UI Core

**Branch**: `006-chat-ui-core` | **Date**: 2026-04-14 | **Spec**: `specs/006-chat-ui-core/spec.md`  
**Input**: Feature specification from `/specs/006-chat-ui-core/spec.md`  
**Constitution Version**: 1.0.0  
**Source plan document**: `docs/mrag-phase4-frontend-plan.md` (Phase 4, Feature 011)

## Summary

Feature 006 turns the existing frontend shell into a usable chat workspace: the Chat route gains a streaming transcript with markdown-rendered assistant messages, inline citations tied to a responsive source panel, token/latency metadata, conversation switching and deletion, and inline recovery for backend/timeout/connectivity/interrupted-stream failures. The implementation stays inside the existing `frontend/src/` seams from Feature 005: Zustand remains the shared state layer, all network traffic continues to flow through `frontend/src/api/`, and mock mode remains a first-class path so the feature is demoable before the backend addenda land. Where the current backend is incomplete relative to the spec, the plan explicitly degrades gracefully: one-shot `POST /ask-question` remains the fallback path when streaming is unavailable, and conversation/message metadata fields are optional until the FastAPI contracts are extended.

## Technical Context

**Language/Version**: TypeScript 5.8.x (strict mode, `noUncheckedIndexedAccess: true`), React 18.3.x, Node.js 20 LTS for tooling  
**Primary Dependencies**: Existing frontend stack from Feature 005 (`react`, `react-router-dom`, `zustand`, `axios`, `tailwindcss`, `msw`, `vitest`, `@testing-library/react`, `@axe-core/react`) plus `react-markdown`, `remark-gfm`, and `unist-util-visit` for markdown/citation rendering  
**Storage**: Browser `localStorage` remains limited to the existing settings store; chat transcript state, focused message state, and in-flight request state remain in-memory and are rehydrated from backend or MSW responses  
**Testing**: Vitest + React Testing Library for component/integration coverage, MSW 2 for mock-mode and API-boundary tests, `@axe-core/react` for automated accessibility checks across empty/streaming/error/populated states, existing `npm run lint`, `npm run typecheck`, `npm run build`, and `npm run build:check` gates  
**Target Platform**: Modern evergreen browsers (latest two Chrome, Edge, Firefox, Safari), responsive from 360px to 2560px, ES2020+ output via Vite 5  
**Project Type**: Web application frontend (SPA) that consumes the Phase 3 FastAPI backend under `src/mrag/api/` strictly through the typed API seam in `frontend/src/api/`  
**Performance Goals**: First visible token under 2 seconds against a warm streaming backend (SC-001), cached full response under 3 seconds (SC-001), existing conversation with up to 100 messages loads into a usable transcript under 1 second on modern hardware (SC-006), zero critical automated a11y violations on the Chat page across required states (SC-004)  
**Constraints**: No direct `fetch`/`axios` usage outside `frontend/src/api/`; frontend must remain fully usable in mock mode with no backend (FR-039, SC-010); UTF-8 and RTL text must render correctly (FR-036); missing backend addenda must degrade by omission rather than placeholder artefacts (FR-020, SC-008); one in-flight request per active conversation with clean cancellation on conversation switch (FR-026)  
**Scale/Scope**: One primary chat workspace plus a history-management surface, ~15–20 new frontend source files, targeted updates to existing stores/api/mocks/layout/pages/tests, up to 100 rendered messages per loaded conversation, one active stream at a time

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This is a frontend-only feature layered on top of the existing backend modules. The constitution was written around the system as a whole, so some articles apply directly, while the retrieval/generation articles apply here as consumer-side constraints rather than implementation work.

| Article | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| I — Modular Architecture | Independent modules with explicit I/O contracts | PASS | The feature stays inside the existing frontend module boundary and further separates API, hooks, stores, chat components, conversation components, and mocks. Components do not call the backend directly; orchestration lives in hooks and the API seam. |
| II — Data Integrity & Preprocessing Discipline | Validation at every boundary | PASS | Backend payloads are normalised in one place, message/source metadata is modeled explicitly, and missing optional fields are omitted rather than guessed. Conversation hydration and retry flows use typed DTOs and deterministic state transitions. |
| III — Multilingual-First Design | UTF-8 throughout, no ASCII-only assumptions | PASS | The UI keeps browser-native UTF-8 handling, preserves `dir="auto"`/text direction for message content, and avoids ASCII-only truncation logic. Citation parsing only targets bracket markers in assistant markdown and leaves all other text untouched. |
| IV — Retrieval Quality Over Speed | Accuracy wins when it conflicts with speed | PASS (consumer side) | This feature does not change retrieval behaviour; it exposes retrieval sources and relevance signals as returned by the backend and does not invent or re-rank sources client-side. |
| V — LLM Integration as a Replaceable Contract | Unified LLM/provider abstraction | PASS (consumer side) | The frontend continues to treat the backend as the only contract. No provider-specific logic or model-specific assumptions enter the UI implementation. |
| VI — Testing & Evaluation as First-Class Citizens | Unit/integration coverage and measurable gates | PASS | The plan adds unit coverage for chat state and streaming parsing, integration coverage for chat/historical flows in mock mode, and automated a11y assertions for all required states. |
| VII — API Design & Error Handling Standards | Consistent Pydantic/error envelope | PASS | All backend failures continue to be normalised into the shared `{ error, detail, status_code }` envelope or the existing `ApiError` discriminated union, and the plan records the specific backend addenda needed for streaming and conversations. |
| VIII — Performance & Caching Discipline | Measured, data-driven performance work | PASS | The UI only displays cache/latency signals sourced from backend metrics, introduces no speculative client caching beyond the existing settings store, and deliberately defers transcript virtualization until the measured 100-message target is exceeded. |
| IX — Code Quality & Development Standards | Strict typing, linting, configuration discipline | PASS | The feature uses the established TypeScript strict/lint/test/build gates, keeps runtime configuration in `import.meta.env`, and extends the existing structured logger rather than adding ad-hoc console usage in feature code. |
| X — Documentation Separation of Concerns | Spec = WHAT, Plan = HOW | PASS | The spec remains technology-agnostic; this plan, `research.md`, `data-model.md`, and the contracts capture all implementation choices and backend/frontend boundary details. |

**No violations.** The only notable constraint is backend incompleteness relative to the spec; the design addresses it with typed fallbacks and explicit addenda instead of weakening the frontend contract.

## Project Structure

### Documentation (this feature)

```text
specs/006-chat-ui-core/
├── plan.md                    # This file (/speckit.plan output)
├── research.md                # Phase 0 output
├── data-model.md              # Phase 1 output
├── quickstart.md              # Phase 1 output
├── contracts/                 # Phase 1 output
│   ├── chat_api.md            # Typed API + streaming + backend addenda contract
│   ├── state_and_ui.md        # Store/hook/component orchestration contract
│   └── mock_mode.md           # MSW handlers and scenario contract
├── checklists/
│   └── requirements.md        # Already passing
└── tasks.md                   # Phase 2 output (/speckit.tasks; not created here)
```

### Source Code (repository root)

```text
frontend/
├── package.json
├── src/
│   ├── api/
│   │   ├── client.ts                  # existing Axios/error normalization
│   │   ├── endpoints.ts               # update one-shot and conversation wrappers
│   │   ├── streaming.ts               # NEW fetch-based SSE adapter inside the API seam
│   │   └── types.ts                   # extend question/conversation/source/message DTOs
│   ├── components/
│   │   ├── chat/                      # NEW feature area
│   │   │   ├── ChatWorkspace.tsx
│   │   │   ├── ChatComposer.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── MessageMeta.tsx
│   │   │   ├── InlineAssistantState.tsx
│   │   │   ├── JumpToLatestButton.tsx
│   │   │   ├── SourcePanel.tsx
│   │   │   └── SourceCard.tsx
│   │   ├── conversations/             # NEW shared list/row/confirm surfaces
│   │   │   ├── ConversationList.tsx
│   │   │   ├── ConversationListItem.tsx
│   │   │   └── DeleteConversationConfirm.tsx
│   │   └── layout/
│   │       ├── AppShell.tsx           # update shell sizing/secondary actions
│   │       ├── Header.tsx             # update “New chat” affordance and active title slot
│   │       └── Sidebar.tsx            # update history/new-chat navigation affordances
│   ├── hooks/
│   │   ├── useHealthCheck.ts          # existing
│   │   ├── useChatSession.ts          # NEW submit/cancel/retry/select orchestration
│   │   ├── useConversationHistory.ts  # NEW summary/detail loading orchestration
│   │   └── useTranscriptScroll.ts     # NEW auto-scroll + jump-to-latest management
│   ├── lib/
│   │   ├── cn.ts
│   │   ├── logger.ts
│   │   ├── formatters.ts              # NEW timestamps, latency, tokens, confidence helpers
│   │   ├── markdown.tsx               # NEW markdown component mapping
│   │   └── remarkCitations.ts         # NEW citation parsing plugin
│   ├── mocks/
│   │   ├── data.ts                    # extend message/source/metadata fixtures
│   │   ├── handlers.ts                # extend one-shot + streaming + conversation scenarios
│   │   └── browser.ts
│   ├── pages/
│   │   ├── ChatPage.tsx               # replace placeholder with full workspace
│   │   ├── HistoryPage.tsx            # replace placeholder with conversation management view
│   │   └── SettingsPage.tsx
│   ├── stores/
│   │   ├── chatStore.ts               # extend rich message status + focus state
│   │   ├── conversationStore.ts       # extend detail loading/deletion orchestration
│   │   └── settingsStore.ts
│   └── styles/
│       └── globals.css                # extend chat/source/history layout styles
└── tests/
    ├── integration/
    │   ├── test_chat_page.tsx
    │   ├── test_history_page.tsx
    │   └── test_streaming_flow.tsx
    ├── unit/
    │   ├── api/
    │   │   ├── test_client.ts
    │   │   └── test_streaming.ts
    │   ├── lib/
    │   │   └── test_remarkCitations.ts
    │   └── stores/
    │       ├── test_chatStore.ts
    │       └── test_conversationStore.ts
    └── setup.ts

src/mrag/api/                           # existing backend integration target; no code changes in this feature
tests/                                  # existing Python test suites remain unchanged
```

**Structure Decision**: Keep Feature 006 entirely within the existing `frontend/` application and the already-established API seam from Feature 005. The feature adds chat-specific components, orchestration hooks, markdown/citation utilities, and richer store state, but it does not introduce a second frontend state library, a component-framework reset, or a new transport layer outside `frontend/src/api/`. Backend work remains explicit follow-up addenda against `src/mrag/api/` rather than being silently assumed into the frontend implementation.

## Architecture

### Runtime flow

1. `ChatPage` renders `ChatWorkspace`, which composes the transcript, composer, source panel, and conversation rail/history affordances.
2. `useChatSession()` coordinates `chatStore`, `conversationStore`, and `settingsStore`.
3. On submit:
   - A user message is appended immediately.
   - An assistant placeholder enters `thinking` state.
   - The hook attempts `streamAnswer()` from `frontend/src/api/streaming.ts` when streaming is enabled.
   - If streaming is disabled, unavailable, or returns a non-streaming capability error, the hook falls back to `askQuestion()` from `endpoints.ts`.
4. Streaming tokens append in place to the assistant message. Final metadata (sources, token usage, latency, confidence/fallback flags, conversation id) is merged on completion.
5. The focused or newest assistant message drives `SourcePanel`; citation activation updates focus and scrolls/highlights the matching source card.
6. `useConversationHistory()` loads conversation summaries and selected conversation detail through the same API seam. Switching or deleting an active conversation first cancels any in-flight request, then replaces the chat transcript with the selected conversation’s persisted messages or the empty-state welcome view.

### Critical invariants

1. **Single network boundary**: components and stores never call `fetch` or `axios` directly. One-shot calls live in `endpoints.ts`; streaming lives in `api/streaming.ts`; both return typed results that the hooks consume.
2. **One in-flight request per active conversation**: the hook owns the live `AbortController`; the store tracks only the serializable request/message ids and status metadata needed for rendering.
3. **Terminal assistant states are explicit**: completed, cancelled, interrupted, and error messages are visually distinct and never collapse into the same UI treatment.
4. **Conversation switching is cancellation-first**: selecting or deleting a conversation while streaming always cancels the previous request before the transcript is replaced.
5. **Optional metadata is never synthesized**: if sources, latency, token usage, or fallback/confidence flags are absent, those surfaces are hidden or reduced to a documented empty state instead of displaying guessed values.
6. **History and chat reuse the same state contracts**: the History route is not a separate implementation path; it consumes the same stores and list/detail hooks as the chat workspace.

### Key technical decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Streaming transport | `fetch` + `ReadableStream` parser inside `frontend/src/api/streaming.ts`, reading SSE-style events from `POST /ask-question/stream` | Browser Axios is awkward for incremental text streaming. Keeping the transport inside the API seam satisfies FR-037 while enabling token-by-token updates and a clean fallback to one-shot `/ask-question`. |
| Fallback behaviour | Automatic downgrade to existing `askQuestion()` when streaming is disabled, 404/501, or otherwise unavailable | The spec explicitly requires graceful degradation when backend addenda are not yet shipped. This keeps the rest of the feature demoable without blocking on streaming. |
| Markdown rendering | `react-markdown` + `remark-gfm`, no raw HTML rendering | Covers headings/lists/code/bold/italic from FR-006 while keeping output safe and predictable. Raw HTML passthrough is intentionally omitted. |
| Citation mapping | Local `remarkCitations` plugin built on `unist-util-visit` | Lets the UI turn only valid `[N]` markers into interactive citation controls while leaving unmatched markers as plain text, which directly matches the edge-case requirement. |
| Transcript rendering | Standard DOM list + scroll manager, no virtualization in this feature | The measured target is 100 messages, which is comfortably within unvirtualized React rendering. Virtualization complicates streaming, focus, citation scrolling, and source synchronization for little gain at this scale. |
| State architecture | Extend the existing Zustand stores; keep async orchestration in hooks instead of introducing TanStack Query | Feature 005 already established store-based state. Streaming, cancellation, and retry fit better in explicit controller hooks than in a cache-oriented query library. |
| Responsive source layout | Persistent side panel on desktop; stacked/bottom panel on narrow viewports using regular page layout, not a new modal framework | Meets FR-016 without introducing a late design-system dependency that the current repo does not otherwise use. |
| Error treatment | Inline assistant-state rendering backed by a message status machine and shared `ApiError` taxonomy | Ensures backend, timeout, connectivity, interrupted, and cancelled paths remain consistent, testable, and recoverable. |

### Backend addenda tracked by this plan

The frontend work can proceed in mock mode without these changes, but the real-backend path will remain partial until the following addenda land in Feature 004:

| Id | Change | Current repo status |
|----|--------|---------------------|
| BE-006-A1 | Add `POST /ask-question/stream` returning SSE-style incremental events | Not present in `src/mrag/api/routes/` today |
| BE-006-A2 | Ensure both one-shot and streaming ask routes create/return a `conversation_id` when a new conversation is started with no incoming id | Current `POST /ask-question` echoes the request id and does not create one when absent |
| BE-006-A3 | Add `GET /conversations`, `GET /conversations/{id}`, and `DELETE /conversations/{id}` | Not present in `src/mrag/api/app.py` today, though persistence tables/repos exist |
| BE-006-A4 | Enrich conversation-detail assistant messages with optional `sources`, `token_usage`, `latency`, `confidence_score`, and `is_fallback` fields | Not present in current frontend/backend DTOs |
| BE-006-A5 | Keep the frontend dev origin in backend CORS configuration for local real-backend testing | Middleware exists; config still needs the origin value in local env/config |

These addenda are documented in `contracts/chat_api.md` so the frontend implementation can guard them explicitly rather than inferring undocumented behaviour.

## Complexity Tracking

No constitution violations or special complexity exceptions were required for this plan.
