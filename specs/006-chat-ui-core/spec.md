# Feature Specification: Chat UI Core

**Feature Branch**: `006-chat-ui-core`
**Created**: 2026-04-14
**Status**: Draft
**Input**: User description: "after accepting and implementing the plan @specs/005-frontend-foundation/plan.md we need to continue build the remaining plan in @docs/mrag-phase4-frontend-plan.md — Chat UI Core — chat window, streaming responses, source citations, token/latency display, conversation switching, error handling"

## Overview

This feature delivers the core conversational experience of the Multilingual RAG Platform on top of the shell scaffolded in Feature 005 (Frontend Foundation). It replaces the Chat and History placeholder pages with a working chat interface where a user can ask a question, watch the answer stream in, inspect the retrieved source chunks and quality signals (confidence, token usage, latency), switch between prior conversations, and recover gracefully from errors or low-confidence backend responses.

Model selection, retrieval-parameter tuning, export, and analytics are intentionally **out of scope** — they are owned by the subsequent "Advanced Chat Features & Settings" feature in the source plan (`docs/mrag-phase4-frontend-plan.md`, Feature 012). This feature also does not modify the backend; any backend extensions required to power the UI are documented in the Assumptions section as pending integration points that this feature consumes through the typed API boundary established in Feature 005.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask a question and see the answer rendered conversationally (Priority: P1)

A user opens the Chat page, types a question in a familiar chat input, and submits it. Their question appears immediately as a "user" message; the system shows a visible "thinking" state while retrieval and generation happen; then the assistant's answer appears as a second message, progressively filling in as text arrives from the backend (token-by-token streaming). Rich text — headings, code blocks, inline code, bulleted/numbered lists, bold and italics — is rendered as formatted content, not raw markdown characters.

**Why this priority**: Without this, nothing else in the feature is reachable. It is the minimum viable slice that delivers the primary product value (asking a question and getting an answer) and is a prerequisite for every other story in this feature.

**Independent Test**: With a seeded mock backend, a user can type "What is the capital of France?", press Enter, watch the message appear, see an activity indicator, and then watch the streamed answer appear with any markdown formatted correctly. Verifiable end-to-end without any of the other user stories implemented.

**Acceptance Scenarios**:

1. **Given** the Chat page is open and the input is empty, **When** the user types a non-empty question and presses Enter, **Then** their question appears as a user-attributed message in the chat transcript and the input field clears.
2. **Given** a user has just submitted a question, **When** the backend has not yet sent any response tokens, **Then** a visible, non-blocking activity/"thinking" indicator is shown in place of the pending assistant message.
3. **Given** the backend is streaming a response, **When** new text arrives, **Then** the assistant message grows incrementally in place (no flicker, no layout jump), and a cursor or equivalent in-progress affordance is shown until the stream ends.
4. **Given** a completed assistant response containing markdown (headings, code fences, lists, bold/italic), **When** the message is displayed, **Then** each markdown construct is rendered as formatted content, not as literal markdown syntax.
5. **Given** the user presses Shift+Enter in the input, **When** the keystroke is received, **Then** a newline is inserted in the input without submitting the message.
6. **Given** a request is in flight, **When** the user attempts to submit a second question, **Then** either submission is disabled until the previous response completes, or a clear affordance to cancel the in-flight response is offered and works (cancellation stops the stream and leaves the partial response marked as cancelled).
7. **Given** the chat transcript is longer than the viewport, **When** a new message or streamed token arrives, **Then** the transcript auto-scrolls to the newest content unless the user has scrolled up, in which case a "jump to latest" affordance appears instead of stealing scroll.

---

### User Story 2 - Inspect the source chunks behind an answer (Priority: P1)

Because the platform is retrieval-augmented, every substantive answer is grounded in retrieved document chunks. The user needs to see which chunks were used, how relevant each was, and trace the answer back to its sources. Inline citation markers in the answer (e.g. [1], [2]) correspond to cards in a sources view that shows the chunk text, a relevance score, the source document identifier, and metadata such as question type and domain. Activating a citation reveals or scrolls to the matching source card.

**Why this priority**: This is what distinguishes a RAG product from a generic chatbot and is a core trust signal. It is P1 alongside the chat window because grounded answers without visible sources would undermine the product's core value proposition. It is independently valuable: even with only the most recent message visible, a user can already verify answers against sources.

**Independent Test**: Ask a factual question whose mock response includes three retrieved chunks. Verify citation markers [1], [2], [3] appear inline in the answer, a sources view lists three cards with chunk text and score, and activating a marker highlights/scrolls to the corresponding card. Also verify that an answer with no retrieved sources (fallback path) displays an explicit "no sources" state rather than an empty list.

**Acceptance Scenarios**:

1. **Given** an assistant message whose backend payload contains a non-empty sources list, **When** the message is rendered, **Then** a sources view associated with that message lists each source, including the chunk text, a relevance score displayed both numerically and visually (e.g. a proportional bar), the originating document identifier, a domain/topic tag, and the chunk's position within its document (e.g. "chunk 3 of 12").
2. **Given** the same assistant message, **When** the user reads the answer body, **Then** any `[N]` citation markers that correspond to returned sources are rendered as visually distinct, interactive affordances (not plain text).
3. **Given** an assistant message is displayed with citations, **When** the user activates a citation marker (by click or keyboard), **Then** the sources view opens if hidden and the corresponding source is brought into view and visibly emphasised.
4. **Given** a sources view card with a long chunk text, **When** the user toggles its expansion control, **Then** the full chunk text becomes visible; the default is a truncated preview.
5. **Given** an assistant message flagged by the backend as a fallback / no-retrieval response, **When** the sources view is inspected, **Then** it shows an explicit "No sources were used for this response" state rather than an empty container or a prior message's sources.
6. **Given** the user switches between messages in the transcript, **When** a new message is focused (by scroll, click, or after new activity), **Then** the sources view reflects the sources for the focused or most recent assistant message rather than staying stuck on a previous message's sources.
7. **Given** a narrow viewport (≤768px wide), **When** the sources view is opened, **Then** it is presented in a layout appropriate for that width (e.g. a full-width drawer or stacked panel) without obscuring the input or breaking the chat layout.

---

### User Story 3 - See performance and cost signals for each answer (Priority: P2)

This is an interview-assessment product intended for technical evaluation: users need visibility into the system's performance and cost per question. Each assistant message carries a compact footer showing token usage and total response time, plus a cache-hit indicator when applicable. A more detailed breakdown (prompt vs. completion tokens; retrieval vs. generation vs. total latency) is available on demand.

**Why this priority**: Important for product credibility and evaluation, but strictly secondary to having working chat with sources. The feature remains usable and demoable without this surface, so it is P2. It is independently testable against the same mock payloads used for US-1 and US-2.

**Independent Test**: Given a mock assistant response whose payload includes `token_usage` and a latency breakdown, verify the compact footer on that message shows a total token count, a total response time, and a cache-hit badge when applicable; activating the footer reveals a detailed breakdown showing prompt tokens, completion tokens, embedding latency, search latency, and generation latency.

**Acceptance Scenarios**:

1. **Given** an assistant message whose backend payload includes token-usage data, **When** the message is rendered, **Then** a compact metadata footer shows the total token count and total response time.
2. **Given** the same message and a cache-hit flag in the payload, **When** the footer is rendered, **Then** an unambiguous cache-hit indicator is shown; when the flag is absent or false, no such indicator is shown.
3. **Given** the metadata footer, **When** the user activates it (click or keyboard), **Then** a detailed breakdown is displayed showing at minimum: prompt token count, completion token count, retrieval/search latency, generation latency, and total latency.
4. **Given** the backend payload is missing one or more of the performance fields (for example, the backend has not yet shipped the schema extension), **When** the message is rendered, **Then** the footer hides the missing signals gracefully rather than showing "NaN", "0", or "undefined", and the rest of the message still renders normally.

---

### User Story 4 - Start, switch between, and revisit conversations (Priority: P2)

Users frequently run multiple parallel lines of inquiry. They need to be able to start a fresh conversation, see a list of prior conversations, activate one to load its full message history into the chat window, and start a new one at any time without losing the current one. Each conversation has an auto-generated title (derived from its first user message), a timestamp, and a message count.

**Why this priority**: High value but not MVP — a single-conversation chat is still demonstrable and usable for the core retrieval/grounding demo. Therefore P2. Independently testable because the backend already exposes conversation CRUD (per Feature 004).

**Independent Test**: Ask two distinct questions in sequence with "New Chat" pressed between them. Confirm the conversation list shows two conversations with auto-generated titles and timestamps. Activate each in turn and verify the chat window loads that conversation's full transcript including sources and metadata.

**Acceptance Scenarios**:

1. **Given** at least one conversation has been persisted, **When** the user opens the app or navigates to the Chat page, **Then** a list of prior conversations is visible (in the sidebar or on the History page) showing an auto-generated title, a timestamp, and a message count for each.
2. **Given** the user is viewing a prior conversation, **When** the user activates "New Chat", **Then** the chat transcript is cleared to a welcome/empty state, the conversation list highlights no active conversation, and the next question submitted starts a new conversation (which appears in the list).
3. **Given** a list of prior conversations, **When** the user activates one, **Then** the full message history for that conversation is loaded into the chat window — including assistant messages with their sources and metadata where persisted — and the list indicates which conversation is active.
4. **Given** the user is mid-stream in one conversation, **When** they attempt to switch conversations, **Then** either the switch is deferred until streaming completes or the in-flight stream is cancelled cleanly before the new conversation loads; in neither case does the loaded conversation end up with partial/streaming messages from the previous one.
5. **Given** a conversation with many messages (e.g. 100+), **When** it is loaded, **Then** the transcript renders without noticeable UI stalling on modern hardware and scrolls smoothly.
6. **Given** a conversation in the list, **When** the user activates its delete control and confirms, **Then** it is removed from the list and (if currently active) the view returns to an empty/welcome state; a cancellation path is available in the confirm step.

---

### User Story 5 - Recover gracefully from errors and low-confidence answers (Priority: P2)

Things go wrong: the backend goes down, a request times out, a stream drops mid-response, the model returns a low-confidence/fallback answer. The user must never see a blank screen, a raw stack trace, or a silently dropped message. Instead, errors are surfaced inline in the chat as a recoverable state with a retry affordance, and low-confidence/fallback answers are marked visually so the user understands what they are looking at.

**Why this priority**: Equal to US-4 in priority — essential for perceived reliability but not strictly blocking the happy-path demo. P2.

**Independent Test**: Force the mock backend to return a 500, a network error, a timeout, an interrupted stream, and a low-confidence fallback response across separate questions. For each, verify the user sees an appropriate in-chat treatment (error bubble with retry, amber low-confidence indicator, etc.) and can continue asking further questions.

**Acceptance Scenarios**:

1. **Given** a submitted question, **When** the backend returns a non-2xx response with an error envelope, **Then** an inline error message is shown in the transcript where the assistant message would have been, including a user-readable explanation and a Retry control; the transcript does not lose the user's original message.
2. **Given** an inline error message, **When** the user activates Retry, **Then** the original user message is resubmitted as a new request and the error state is replaced by the activity indicator, then by the resulting assistant message or a fresh error state.
3. **Given** a submitted question, **When** the request exceeds the configured client-side timeout with no response, **Then** the inline error state explicitly communicates a timeout (distinct from a generic error) and offers Retry.
4. **Given** a submitted question, **When** there is no network connectivity (offline/DNS failure), **Then** the inline error state explicitly communicates a connectivity problem (distinct from a backend error) and offers Retry.
5. **Given** a successful assistant message whose backend payload indicates a low-confidence or fallback response, **When** the message is rendered, **Then** a visually distinct indicator (e.g. an amber accent and a "Low confidence" label) is displayed alongside the message, with an on-demand explanation of what it means.
6. **Given** any error state in any message, **When** the user submits a new, unrelated question, **Then** the new request proceeds normally, independent of the previous error.

---

### Edge Cases

- **Empty or whitespace-only input**: the submit control is disabled and Enter does not submit; the user is not left wondering why their message "disappeared".
- **Extremely long input**: input that exceeds any backend-enforced character/token limit is either prevented at the client with a clear indicator or submitted and surfaced as a recoverable backend error — never silently truncated.
- **Extremely long answer**: markdown answers with very long content (e.g. large code blocks) wrap or scroll correctly within the assistant message bubble and do not cause horizontal page scroll.
- **Streaming interruption**: if the network drops mid-stream, the partial answer is preserved in the transcript, marked as interrupted, and a retry affordance is offered.
- **User cancels a stream**: cancellation is reflected unambiguously (the partial answer is marked as cancelled rather than looking like it completed normally).
- **Switch conversations mid-stream**: the in-flight stream is cancelled cleanly; the loaded conversation does not inherit streaming state from the prior one.
- **Delete the active conversation**: the view returns to the welcome/empty state; no broken reference to a conversation identifier that no longer exists.
- **Citation marker with no matching source**: the marker is rendered as plain text rather than a broken interactive element.
- **Backend payload missing optional fields** (e.g. pre-addenda backend): the UI degrades gracefully, hiding missing signals rather than showing placeholders like `NaN` or `undefined`.
- **Very wide (≥2560px) and very narrow (360px) viewports**: chat layout, sources view, and conversation list remain usable; the sources view does not overlap the input on narrow viewports.
- **Non-Latin and right-to-left text**: user and assistant messages containing non-Latin scripts (Arabic, CJK, Cyrillic, etc.) render correctly, preserve text direction, and do not break citation parsing.
- **Keyboard-only navigation**: every interactive affordance (send, cancel, retry, citation, source-expand, conversation switch/delete, metadata-footer expand) is reachable and operable via keyboard with a visible focus state.

## Requirements *(mandatory)*

### Functional Requirements

**Chat window & messaging**

- **FR-001**: System MUST provide a chat transcript view listing alternating user and assistant messages in submission order, with clear visual attribution of each message's role.
- **FR-002**: Users MUST be able to compose a question in a multi-line input, submit it via Enter, and insert a newline via Shift+Enter.
- **FR-003**: System MUST prevent submission of empty or whitespace-only input and communicate that state visually (e.g. a disabled send control).
- **FR-004**: System MUST display an explicit in-progress indicator from the moment a question is submitted until the first response content is received.
- **FR-005**: System MUST render assistant responses as they stream from the backend, appending new content to the in-progress message without re-rendering or losing prior content, and MUST show a clear in-progress affordance until the stream ends.
- **FR-006**: System MUST render assistant messages with markdown formatting, including at minimum: headings, paragraphs, ordered and unordered lists, bold and italic text, inline code, and fenced code blocks.
- **FR-007**: System MUST auto-scroll the transcript to the newest content as messages and streamed tokens arrive, UNLESS the user has manually scrolled away from the bottom, in which case a "jump to latest" affordance MUST be shown instead.
- **FR-008**: Users MUST be able to cancel an in-flight response; a cancelled response MUST be marked as cancelled and MUST NOT appear identical to a completed response.
- **FR-009**: System MUST prevent a second question from being submitted while a previous one is still in flight, OR MUST serialise submissions such that responses appear in submission order.

**Source references & citations**

- **FR-010**: System MUST display, for each assistant message whose backend payload includes retrieved sources, a sources view listing each source with: chunk text, relevance score (numeric and visual), originating document identifier, domain/topic tag, and chunk position within its parent document.
- **FR-011**: System MUST render `[N]` citation markers embedded in the assistant message text as visually distinct, interactive affordances when a matching source exists in the message's sources list.
- **FR-012**: Users MUST be able to activate a citation affordance (by mouse or keyboard) to reveal and visually emphasise the matching source card in the sources view.
- **FR-013**: System MUST provide an explicit "No sources used for this response" state in the sources view when the backend payload indicates a fallback or no-retrieval response, visually distinct from an absent or loading state.
- **FR-014**: System MUST keep the sources view in sync with the user's focus in the transcript (the most recently focused or newest assistant message), rather than staying stuck on a previous message's sources.
- **FR-015**: Source cards MUST default to a truncated preview of the chunk text and provide a user-operable control to expand to the full text.
- **FR-016**: On viewports ≤768px wide, the sources view MUST be presented in a layout that does not obscure the input bar or break the chat layout (for example, a full-width drawer, tab, or stacked panel).

**Token usage & latency**

- **FR-017**: System MUST display, for each completed assistant message whose backend payload includes token-usage data, a compact metadata footer summarising at minimum the total token count and the total response time.
- **FR-018**: System MUST show a distinct cache-hit indicator in the metadata footer when the backend payload flags the response as a cache hit, and MUST NOT display such an indicator otherwise.
- **FR-019**: Users MUST be able to activate the metadata footer to see a detailed breakdown including prompt tokens, completion tokens, retrieval/search latency, generation latency, and total latency.
- **FR-020**: System MUST gracefully omit any individual metadata field (token counts, latency components, cache flag) that is missing from the backend payload, without displaying placeholder artefacts such as `NaN`, `undefined`, or `0 ms` when the true value is unknown.

**Conversation management**

- **FR-021**: System MUST display a list of prior conversations, each labelled with an auto-generated title derived from the conversation's first user message, a timestamp, and a message count.
- **FR-022**: Users MUST be able to start a new conversation from any screen; starting a new conversation MUST clear the transcript to a welcome/empty state and MUST NOT delete or modify any existing conversation.
- **FR-023**: Users MUST be able to switch to an existing conversation; switching MUST load that conversation's full message history, including assistant messages with their sources and metadata where persisted.
- **FR-024**: System MUST indicate in the conversation list which conversation is currently active.
- **FR-025**: Users MUST be able to delete a conversation from the list after an explicit confirmation step that includes a cancel path; if the deleted conversation was active, the view MUST return to an empty/welcome state.
- **FR-026**: System MUST ensure that switching conversations while a response is streaming does not leave the newly loaded conversation with partial or leaked streaming state from the previous conversation.

**Error handling & low-confidence states**

- **FR-027**: System MUST surface backend errors inline in the transcript (not as a modal, toast-only, or console-only notification), preserve the user's original message, and offer a Retry control that resubmits the original message.
- **FR-028**: System MUST visually distinguish between at least three error categories and communicate them in user-readable terms: backend error (the service responded with an error envelope), timeout (the client-side deadline elapsed), and connectivity error (no response reachable).
- **FR-029**: System MUST handle an interrupted stream (network drop mid-response) by preserving any partial content already rendered, marking the message as interrupted, and offering a Retry control.
- **FR-030**: System MUST visually mark assistant messages whose backend payload flags them as fallback or low-confidence (for example with an amber accent and an explicit label), and MUST provide an on-demand explanation of what the mark means.
- **FR-031**: System MUST allow the user to submit new questions regardless of the state of any previous message; no single failed message may block further use of the chat.

**Accessibility & layout**

- **FR-032**: Every interactive affordance introduced by this feature (send, cancel, retry, citation marker, source expand, conversation switch/delete, metadata-footer expand) MUST be reachable and operable via keyboard alone with a visible focus indicator.
- **FR-033**: Every interactive affordance MUST have an accessible name (either visible text or an equivalent accessible label) and MUST meet WCAG AA contrast in both light and dark themes.
- **FR-034**: System MUST pass automated accessibility checks with zero critical violations on the Chat page across the states: empty, streaming, error, populated with sources, and low-confidence.
- **FR-035**: System MUST render a usable chat layout across viewports from 360px to 2560px wide, including correct placement or adaptation of the sources view on narrow viewports.
- **FR-036**: System MUST preserve text direction and correct rendering for non-Latin and right-to-left scripts in both user and assistant messages.

**Integration boundaries**

- **FR-037**: System MUST route all backend calls made by this feature through the single typed API integration seam established in Feature 005, so no component or hook introduces a parallel HTTP path.
- **FR-038**: System MUST normalise every backend failure into the shared error envelope defined in Feature 005 before surfacing it in the UI, so error rendering logic does not vary per call site.
- **FR-039**: System MUST operate end-to-end in mock mode (no real backend) using the mock layer from Feature 005 extended with handlers for streaming, conversations, and sources, so the feature is independently demoable and testable.

### Key Entities *(include if feature involves data)*

- **ChatMessage**: A single entry in a conversation transcript. Attributes: stable identifier, role (user or assistant), textual content (possibly markdown, possibly partial while streaming), submission/completion timestamps, the conversation it belongs to, optional retrieved sources (assistant only), optional token usage and latency breakdown (assistant only), optional confidence and fallback flags (assistant only), optional streaming/interrupted/cancelled/error flags for UI state.
- **Conversation**: An ordered thread of ChatMessages sharing a single topic. Attributes: stable identifier, auto-generated title derived from the first user message, created/last-updated timestamps, message count, full message list (loaded on demand).
- **RetrievalSource**: A single document chunk used to ground an assistant message. Attributes: stable chunk identifier, the chunk text, a relevance score in [0, 1], the originating document identifier, a domain/topic tag, the chunk's index and the total chunks in its parent document, and optionally the original question and answer this chunk was extracted from.
- **TokenUsage**: The token accounting for a single assistant message. Attributes: prompt tokens, completion tokens, total tokens.
- **LatencyBreakdown**: The timing accounting for a single assistant message. Attributes: embedding/retrieval latency, search latency, generation latency, total latency, cache-hit flag.
- **InFlightRequest**: The ephemeral state of an in-progress question. Attributes: pending assistant message identifier, cancellation handle, submission timestamp. Not persisted.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can submit a question and see the first token of the assistant's response begin to appear in under 2 seconds on a typical home broadband connection with a warm backend; the full response for a cached query completes in under 3 seconds end-to-end.
- **SC-002**: In 100 consecutive sampled responses containing retrieved sources, 100% of `[N]` citation markers present in the answer text and backed by a returned source are rendered as interactive, working affordances that reveal the correct source.
- **SC-003**: In user testing, at least 95% of participants can, without assistance, (a) send a question, (b) identify and open the source(s) behind an answer, and (c) start a new conversation, on their first attempt.
- **SC-004**: Zero critical accessibility violations are reported by automated accessibility checks on the Chat page across the states: empty, streaming, populated with sources, error, and low-confidence.
- **SC-005**: The chat layout renders without overlap, clipping, or broken interactive affordances across viewports from 360px to 2560px wide.
- **SC-006**: Loading an existing conversation of up to 100 messages renders a usable, scrollable transcript in under 1 second on modern consumer hardware.
- **SC-007**: Every backend failure class (backend error, timeout, connectivity error, interrupted stream) produces a user-readable inline treatment in the chat with a working Retry path; zero failures result in a blank screen, silent drop, or uncaught exception surfacing to the console as an error.
- **SC-008**: For a response payload missing any subset of the optional metadata fields (token usage, individual latency components, cache flag, confidence, fallback flag), the message still renders correctly and no placeholder artefacts (`NaN`, `undefined`, empty-but-labelled rows) are displayed.
- **SC-009**: 100% of backend calls made by this feature go through the single typed API integration seam established in Feature 005, verifiable by a repo-wide check finding no direct network calls outside that seam.
- **SC-010**: The entire feature is operable end-to-end with no real backend running, using only the mock layer from Feature 005 extended by this feature; the automated test suite for this feature passes with the backend disabled.

## Assumptions

- **Depends on Feature 005 (Frontend Foundation)** being merged: the AppShell, router, typed API client, error envelope, Zustand store scaffold, theme handling, accessibility tooling, and mock infrastructure are already in place and are reused rather than reimplemented here.
- **Backend streaming is available** via a streaming endpoint for question answering (e.g. Server-Sent Events or a chunked HTTP response) before this feature is demoable end-to-end against real infrastructure. If the streaming endpoint is not yet available, the feature degrades to a single-shot response with the activity indicator held until the full response arrives, without blocking delivery of the rest of the feature.
- **Backend response schema extensions** expose `sources`, `token_usage`, `latency` (per-stage breakdown and cache-hit), `is_fallback`, and `confidence_score` fields on the question-answering response. These extensions are already called out as pending backend addenda in Feature 005's plan. Until they ship, the UI renders the fields that are present and gracefully omits the rest (per FR-020 and SC-008).
- **Backend conversation CRUD endpoints exist** (list, get-by-id, delete) — these are part of the Phase 3 API (Feature 004) already in the repo. This feature consumes them; it does not add or modify backend routes.
- **No authentication in this feature**: the platform continues to operate as a single implicit user; per-user conversation scoping, login, and permissions are out of scope.
- **No model selection, retrieval-parameter tuning, export, or analytics in this feature**: these are owned by the "Advanced Chat Features & Settings" feature in the source plan document. This feature uses the default model and retrieval settings already stored in the settings store from Feature 005.
- **UI language is English**; message content may be any language supported by the backend and must round-trip correctly, but chrome labels and error messages are authored in English.
- **Target browsers** remain the latest two versions of Chrome, Edge, Firefox, and Safari, as established in Feature 005.
- **Client-side token estimation** (showing a live token count as the user types) is considered a nice-to-have and is out of scope for this feature's definition of done; the authoritative token counts come from the backend in the response payload.
