# Tasks: Chat UI Core

**Input**: Design documents from `/specs/006-chat-ui-core/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: Automated tests are required for this feature because the spec calls for mock-mode end-to-end operability, automated accessibility checks, and regression coverage across streaming, conversations, citations, and error handling.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated as an independently testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on unfinished tasks)
- **[Story]**: Which user story this task belongs to (`[US1]` ... `[US5]`)
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the dependencies and configuration gates that the chat feature needs before shared implementation work begins.

- [X] T001 Update frontend markdown/citation dependencies in `frontend/package.json` and `frontend/package-lock.json`
- [X] T002 Update streaming feature flags in `frontend/.env.example`, `frontend/src/config.ts`, and `frontend/src/types/env.d.ts`
- [X] T003 Update API-seam lint safeguards in `frontend/.eslintrc.cjs` and `frontend/tests/unit/api/test_client.ts` so `fetch` is allowed only in `frontend/src/api/streaming.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared DTOs, stores, fixtures, and helper modules that every user story builds on.

**⚠️ CRITICAL**: No user story work should start until this phase is complete.

- [X] T004 Update rich chat and conversation DTOs in `frontend/src/api/types.ts`
- [X] T005 Update lifecycle-aware transcript state in `frontend/src/stores/chatStore.ts` and `frontend/tests/unit/stores/test_chatStore.ts`
- [X] T006 [P] Extend mock chat fixtures and scenario tags in `frontend/src/mocks/data.ts` and `frontend/src/mocks/handlers.ts`
- [X] T007 [P] Create shared transcript helpers in `frontend/src/lib/formatters.ts` and `frontend/src/lib/markdown.tsx`
- [X] T008 [P] Add foundational mock/server support for chat flows in `frontend/tests/setup.ts` and `frontend/tests/integration/test_mock_mode.tsx`

**Checkpoint**: Shared chat infrastructure is ready; user-story work can begin.

---

## Phase 3: User Story 1 - Ask a question and see the answer rendered conversationally (Priority: P1) 🎯 MVP

**Goal**: Replace the Chat placeholder with a working transcript, composer, streaming answer path, markdown rendering, cancellation, and auto-scroll behavior.

**Independent Test**: In mock mode, submit a question from the Chat page and verify immediate user-message rendering, visible thinking state, streamed assistant content, markdown formatting, Shift+Enter newline behavior, cancellation, and jump-to-latest behavior without relying on sources or conversation history.

### Tests for User Story 1

- [X] T009 [P] [US1] Add streaming parser coverage in `frontend/tests/unit/api/test_streaming.ts`
- [X] T010 [US1] Expand happy-path chat rendering coverage in `frontend/tests/integration/test_chat_page.tsx`

### Implementation for User Story 1

- [X] T011 [P] [US1] Create SSE/fallback transport adapter in `frontend/src/api/streaming.ts`
- [X] T012 [P] [US1] Create chat composer and basic assistant-state UI in `frontend/src/components/chat/ChatComposer.tsx` and `frontend/src/components/chat/InlineAssistantState.tsx`
- [X] T013 [P] [US1] Create transcript row components in `frontend/src/components/chat/MessageList.tsx` and `frontend/src/components/chat/MessageBubble.tsx`
- [X] T014 [US1] Create send/cancel and auto-scroll orchestration in `frontend/src/hooks/useChatSession.ts` and `frontend/src/hooks/useTranscriptScroll.ts`
- [X] T015 [US1] Create the chat workspace in `frontend/src/components/chat/ChatWorkspace.tsx`, `frontend/src/components/chat/JumpToLatestButton.tsx`, and `frontend/src/pages/ChatPage.tsx`
- [X] T016 [US1] Update transcript and composer layout behavior in `frontend/src/styles/globals.css` and `frontend/src/components/layout/AppShell.tsx`

**Checkpoint**: User Story 1 should be fully functional as the MVP chat experience.

---

## Phase 4: User Story 2 - Inspect the source chunks behind an answer (Priority: P1)

**Goal**: Add citation-aware markdown rendering and a responsive source panel that stays synchronized with the focused assistant message.

**Independent Test**: With a mock response containing three sources, verify citation markers render inline, activating a citation reveals and highlights the matching source card, source cards expand/collapse, and fallback/no-source responses show an explicit empty state.

### Tests for User Story 2

- [X] T017 [P] [US2] Add citation parsing unit coverage in `frontend/tests/unit/lib/test_remarkCitations.ts`
- [X] T018 [US2] Expand citation and source-panel coverage in `frontend/tests/integration/test_chat_page.tsx`

### Implementation for User Story 2

- [X] T019 [P] [US2] Create citation parsing logic in `frontend/src/lib/remarkCitations.ts`
- [X] T020 [P] [US2] Create source presentation components in `frontend/src/components/chat/SourceCard.tsx` and `frontend/src/components/chat/SourcePanel.tsx`
- [X] T021 [US2] Wire citation focus and source synchronization in `frontend/src/components/chat/MessageBubble.tsx` and `frontend/src/components/chat/ChatWorkspace.tsx`
- [X] T022 [US2] Update responsive source styling and no-source fixture data in `frontend/src/styles/globals.css` and `frontend/src/mocks/data.ts`

**Checkpoint**: User Stories 1 and 2 now deliver a grounded RAG chat UI with inspectable sources.

---

## Phase 5: User Story 3 - See performance and cost signals for each answer (Priority: P2)

**Goal**: Surface token, latency, and cache-hit information per assistant message without breaking when optional metadata is absent.

**Independent Test**: With a mock response containing token and latency fields, verify the assistant footer shows compact totals, expands to detailed timings, and hides any missing fields gracefully without placeholder artefacts.

### Tests for User Story 3

- [X] T023 [P] [US3] Add metadata formatter coverage in `frontend/tests/unit/lib/test_formatters.ts`
- [X] T024 [US3] Expand metadata rendering coverage in `frontend/tests/integration/test_streaming_flow.tsx`

### Implementation for User Story 3

- [X] T025 [P] [US3] Create assistant metadata footer UI in `frontend/src/components/chat/MessageMeta.tsx`
- [X] T026 [US3] Wire optional token and latency rendering in `frontend/src/components/chat/MessageBubble.tsx`, `frontend/src/lib/formatters.ts`, and `frontend/src/api/types.ts`
- [X] T027 [US3] Extend metadata-bearing mock responses and endpoint expectations in `frontend/src/mocks/data.ts` and `frontend/tests/unit/api/test_endpoints.ts`

**Checkpoint**: User Stories 1–3 now cover the main chat, sources, and performance-signal surfaces.

---

## Phase 6: User Story 4 - Start, switch between, and revisit conversations (Priority: P2)

**Goal**: Replace the History placeholder with a reusable conversation-management surface and support new chat, conversation selection, and deletion with clean streaming cancellation.

**Independent Test**: In mock mode, create two conversations, start a new chat between them, switch back and forth, and delete one conversation with an explicit confirm/cancel path while verifying no leaked streaming state appears in the newly loaded transcript.

### Tests for User Story 4

- [X] T028 [US4] Expand conversation management coverage in `frontend/tests/integration/test_history_page.tsx`

### Implementation for User Story 4

- [X] T029 [P] [US4] Extend conversation loading and rollback behavior in `frontend/src/stores/conversationStore.ts` and `frontend/tests/unit/stores/test_conversationStore.ts`
- [X] T030 [P] [US4] Create reusable conversation list UI in `frontend/src/components/conversations/ConversationList.tsx` and `frontend/src/components/conversations/ConversationListItem.tsx`
- [X] T031 [P] [US4] Create explicit delete confirmation and shared history orchestration in `frontend/src/components/conversations/DeleteConversationConfirm.tsx` and `frontend/src/hooks/useConversationHistory.ts`
- [X] T032 [US4] Replace the History placeholder and reuse conversation flows in `frontend/src/pages/HistoryPage.tsx` and `frontend/src/components/chat/ChatWorkspace.tsx`
- [X] T033 [US4] Add new-chat and active-conversation controls in `frontend/src/components/layout/Header.tsx`, `frontend/src/components/layout/Sidebar.tsx`, and `frontend/src/hooks/useChatSession.ts`

**Checkpoint**: User Stories 1–4 now support real chat workflows across multiple conversations.

---

## Phase 7: User Story 5 - Recover gracefully from errors and low-confidence answers (Priority: P2)

**Goal**: Make backend errors, timeouts, interrupted streams, cancellations, and low-confidence/fallback answers recoverable and visually distinct inside the transcript.

**Independent Test**: Use mock scenario tags to trigger backend error, timeout, interrupted stream, and low-confidence/fallback paths; verify inline treatments, retry behavior, preserved partial content, and the ability to continue asking new questions after any failure.

### Tests for User Story 5

- [X] T034 [US5] Expand error and retry coverage in `frontend/tests/integration/test_streaming_flow.tsx`
- [X] T035 [US5] Add accessibility state coverage in `frontend/tests/integration/test_chat_page.tsx`

### Implementation for User Story 5

- [X] T036 [P] [US5] Extend inline assistant-state treatments in `frontend/src/components/chat/InlineAssistantState.tsx` and `frontend/src/components/chat/MessageBubble.tsx`
- [X] T037 [US5] Add retry and interrupted-stream recovery logic in `frontend/src/hooks/useChatSession.ts` and `frontend/src/api/streaming.ts`
- [X] T038 [US5] Finalize deterministic failure and fallback scenarios in `frontend/src/mocks/handlers.ts`, `frontend/src/mocks/data.ts`, and `frontend/src/components/chat/ChatWorkspace.tsx`

**Checkpoint**: All five user stories are independently functional and recoverable in mock mode.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final refinements that span multiple stories.

- [X] T039 [P] Update shell and route regression coverage in `frontend/tests/integration/test_app_shell.tsx` and `frontend/tests/integration/test_routing.tsx`
- [X] T040 [P] Apply final responsive, focus-visible, and RTL-safe polish in `frontend/src/styles/globals.css` and `frontend/src/components/layout/AppShell.tsx`
- [X] T041 Update developer verification guidance in `frontend/README.md` and `specs/006-chat-ui-core/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies; can start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user-story work.
- **Phase 3 (US1)**: Depends on Phase 2; establishes the MVP chat surface.
- **Phase 4 (US2)**: Depends on US1 because citations and source focus extend the transcript/message rendering surfaces.
- **Phase 5 (US3)**: Depends on US1 because metadata renders on assistant messages already built in the chat transcript.
- **Phase 6 (US4)**: Depends on US1 and Phase 2 because conversation switching reuses the chat session and transcript surfaces.
- **Phase 7 (US5)**: Depends on US1 and benefits from US2/US3/US4, but can begin once the base chat session and mock scenarios exist.
- **Phase 8 (Polish)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: No user-story dependency after foundational work; this is the MVP.
- **US2 (P1)**: Depends on US1 transcript/message rendering.
- **US3 (P2)**: Depends on US1 assistant message rendering.
- **US4 (P2)**: Depends on US1 chat session orchestration and foundational mock/state work.
- **US5 (P2)**: Depends on US1 streaming/cancellation flow and foundational mock scenarios.

### Within Each User Story

- Tests should be written first and observed failing before implementation.
- Shared helpers and low-level components come before orchestration hooks and page integration.
- Page and layout integration come after the core story components are implemented.
- Each phase ends at an independently testable checkpoint.

### Parallel Opportunities

- `T006`, `T007`, and `T008` can run in parallel after `T004` and `T005` are underway because they touch different foundational files.
- In **US1**, `T011`, `T012`, and `T013` can run in parallel once the foundational DTO/store work is complete.
- In **US2**, `T019` and `T020` can run in parallel.
- In **US3**, `T023` and `T025` can run in parallel.
- In **US4**, `T029`, `T030`, and `T031` can run in parallel.
- In **US5**, `T036` can proceed in parallel with part of `T034` once the mock scenarios exist.
- `T039` and `T040` can run in parallel during polish.

---

## Parallel Example: User Story 1

```bash
Task: "Create SSE/fallback transport adapter in frontend/src/api/streaming.ts"
Task: "Create chat composer and basic assistant-state UI in frontend/src/components/chat/ChatComposer.tsx and frontend/src/components/chat/InlineAssistantState.tsx"
Task: "Create transcript row components in frontend/src/components/chat/MessageList.tsx and frontend/src/components/chat/MessageBubble.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "Create citation parsing logic in frontend/src/lib/remarkCitations.ts"
Task: "Create source presentation components in frontend/src/components/chat/SourceCard.tsx and frontend/src/components/chat/SourcePanel.tsx"
```

## Parallel Example: User Story 4

```bash
Task: "Extend conversation loading and rollback behavior in frontend/src/stores/conversationStore.ts and frontend/tests/unit/stores/test_conversationStore.ts"
Task: "Create reusable conversation list UI in frontend/src/components/conversations/ConversationList.tsx and frontend/src/components/conversations/ConversationListItem.tsx"
Task: "Create explicit delete confirmation and shared history orchestration in frontend/src/components/conversations/DeleteConversationConfirm.tsx and frontend/src/hooks/useConversationHistory.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational prerequisites.
3. Complete Phase 3: User Story 1.
4. Validate the MVP with `frontend/tests/unit/api/test_streaming.ts`, `frontend/tests/integration/test_chat_page.tsx`, and the mock-mode workflow in `specs/006-chat-ui-core/quickstart.md`.

### Incremental Delivery

1. Ship the MVP chat flow in US1.
2. Add grounded-source trust signals in US2.
3. Add performance/cost visibility in US3.
4. Add multi-conversation workflows in US4.
5. Add resilient failure handling and low-confidence treatments in US5.
6. Finish with shell/regression polish and verification docs.

### Parallel Team Strategy

1. One engineer handles Setup + Foundational phases.
2. After US1 lands, parallelize:
   - Engineer A: US2 (citations and source panel)
   - Engineer B: US3 (message metadata)
   - Engineer C: US4 (conversation management)
   - Engineer D: US5 (error and fallback handling)
3. Rejoin for Phase 8 polish and final regression validation.

---

## Notes

- All tasks follow the required checklist format: checkbox, sequential ID, optional `[P]`, required `[US#]` on story tasks, and exact file paths.
- The suggested MVP scope is **User Story 1 only**.
- The real-backend gaps documented in `contracts/chat_api.md` remain follow-up work outside this frontend feature; the task list assumes mock mode is the authoritative implementation/test path until those addenda land.
