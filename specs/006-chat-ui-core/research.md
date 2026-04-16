# Phase 0 Research: Chat UI Core

**Branch**: `006-chat-ui-core` | **Date**: 2026-04-14 | **Plan**: `plan.md`

This document resolves the implementation choices behind Feature 006 and records the rejected alternatives so future work can extend the chat UI without reopening the same decisions.

---

## R1 — Streaming transport inside the existing API seam

**Decision**: Implement streaming in a new `frontend/src/api/streaming.ts` module using `fetch` + `ReadableStream` parsing of SSE-style events from `POST /ask-question/stream`, with automatic fallback to the existing one-shot `POST /ask-question`.

**Rationale**: The frontend already centralises backend communication in `frontend/src/api/`. Axios remains appropriate for ordinary JSON requests, but browser Axios is not a good fit for incremental text rendering. A small fetch-based streaming adapter inside the same API seam preserves FR-037 while enabling token-by-token updates, cancellation via `AbortController`, and a clean downgrade when the backend addendum has not shipped yet.

**Alternatives considered**:

- **EventSource** — rejected because the chat submission is a `POST` with a JSON body, while `EventSource` only supports `GET`.
- **WebSocket** — rejected because the backend plan already points toward `StreamingResponse`/SSE, and a bidirectional socket adds a protocol the rest of the system does not need.
- **Polling** — rejected because it cannot satisfy the “grows incrementally in place” requirement cleanly and would add needless backend load.
- **Component-level fetch calls** — rejected because it would break the single typed integration seam established in Feature 005.

---

## R2 — Markdown rendering strategy

**Decision**: Use `react-markdown` with `remark-gfm`; do not enable raw HTML rendering.

**Rationale**: The spec requires headings, lists, inline code, fenced code blocks, bold, and italics. `react-markdown` covers that surface cleanly, keeps rendering declarative inside React, and defaults to safe handling of raw HTML. `remark-gfm` adds fenced code/list niceties without forcing a larger rendering stack. Syntax highlighting is explicitly deferred because the spec only requires formatting, not colourized code.

**Alternatives considered**:

- **Manual markdown parsing** — rejected as too error-prone and expensive for the required surface area.
- **`dangerouslySetInnerHTML` after a markdown-to-HTML pass** — rejected on safety and sanitization complexity.
- **Heavier editor/viewer stacks (`markdown-it`, `rehype-raw`, full highlight pipeline)** — rejected because they exceed the feature’s requirements and add more failure modes than value today.

---

## R3 — Citation rendering and matching

**Decision**: Add a local `remarkCitations` plugin backed by `unist-util-visit` that transforms only valid `[N]` markers into interactive citation nodes when `N` maps to a returned source; unmatched markers remain plain text.

**Rationale**: The edge cases explicitly forbid broken interactive citations. A markdown-plugin step lets the UI preserve the authored answer text while selectively upgrading citations into buttons/links tied to source cards. Keeping the logic local also avoids coupling source indexing rules to the markdown library internals beyond a small AST walk.

**Alternatives considered**:

- **Regex replacement on the raw answer string** — rejected because it becomes brittle inside code spans, code fences, and other markdown constructs.
- **Post-render DOM query/replace** — rejected because it fights React’s rendering model and makes keyboard/accessibility behaviour harder to guarantee.
- **Turning every `[N]` into a citation regardless of source availability** — rejected because it violates the “plain text when no matching source exists” edge case.

---

## R4 — Transcript rendering and scroll management

**Decision**: Render the transcript as a normal React list and manage auto-scroll with a dedicated `useTranscriptScroll()` hook; defer virtualization until real evidence shows 100-message conversations exceed the success criteria.

**Rationale**: The required scale is modest. Virtualization complicates three behaviours this feature cares about: incremental streaming, citation-to-source focus, and “jump to latest” behaviour when the user scrolls away from the bottom. For up to 100 messages, the simpler DOM list is easier to reason about and test.

**Alternatives considered**:

- **`@tanstack/react-virtual` now** — rejected as premature; it solves a scale problem the spec does not yet impose.
- **Always forcing scroll-to-bottom** — rejected because FR-007 requires user-controlled scroll preservation.
- **Relying on CSS-only scroll anchoring** — rejected because we need explicit “jump to latest” state and stream-aware bottom detection.

---

## R5 — State orchestration and query libraries

**Decision**: Keep Zustand as the shared state layer and add orchestration hooks (`useChatSession`, `useConversationHistory`) for async work; do not introduce TanStack Query in this feature.

**Rationale**: Feature 005 already established `chatStore` and `conversationStore`. Streaming, cancellation, retry, focused-message sync, and optimistic deletion are controller-style flows rather than cache-centric query flows. Hooks can compose stores and the API seam directly without adding a second state abstraction.

**Alternatives considered**:

- **TanStack Query** — rejected for now because streaming and message-by-message mutation do not map naturally to its request cache model, and the existing store contracts are already in place.
- **Putting all async orchestration into the stores** — rejected because it would mix UI lifecycle concerns (abort handles, scroll focus, retries) into state modules that should stay relatively dumb.
- **React Context/useReducer rewrite** — rejected because the repo already standardized on Zustand.

---

## R6 — Responsive source panel and delete confirmation

**Decision**: Use regular page layout for both concerns: a persistent right-side source panel on desktop, a stacked or bottom panel on small screens, and inline confirmation UI for conversation deletion rather than adding a modal framework mid-feature.

**Rationale**: The current frontend does not ship Radix/shadcn primitives despite the earlier plan mentioning them, and the live repo already uses plain React + Tailwind components. Matching repo reality avoids a design-system pivot in the middle of a feature. The spec only requires an explicit confirmation path and a mobile-safe source layout, not a modal library.

**Alternatives considered**:

- **Introduce Radix Dialog/Drawer now** — rejected because it adds a new dependency family and interaction model not otherwise present in the checked-in frontend.
- **Native `window.confirm()`** — rejected as too blunt for styling, testing, and inline workflow continuity.
- **Keep the source panel desktop-only** — rejected because FR-016 explicitly requires a narrow-viewport adaptation.

---

## R7 — Message lifecycle and error-state modeling

**Decision**: Model assistant messages with explicit terminal and in-flight states: `thinking`, `streaming`, `complete`, `cancelled`, `interrupted`, and `error`, plus `errorKind` sourced from the shared `ApiError` taxonomy.

**Rationale**: The spec distinguishes several behaviours that cannot safely share a single “failed” flag. Cancellation, interrupted streams, backend failures, and timeouts all have different retry and display semantics. A message-status model keeps rendering deterministic and supports retry without losing the user’s original prompt or partial assistant content.

**Alternatives considered**:

- **Single `isStreaming` + optional `error` string** — rejected because it is too weak to represent interrupted/cancelled/low-confidence states cleanly.
- **Store errors globally only** — rejected because the spec requires inline, per-message recovery.
- **Discard partial content on interruption** — rejected because FR-029 explicitly requires preservation.

---

## R8 — Mock-mode strategy for chat scenarios

**Decision**: Extend MSW with both one-shot and streaming handlers plus deterministic scenario triggers in the submitted question text (for example `[mock:fallback]`, `[mock:error]`, `[mock:timeout]`, `[mock:interrupt]`), while tests retain the ability to override handlers directly.

**Rationale**: The feature must remain demoable without a backend. Deterministic scenario tags allow a human tester to exercise happy-path, fallback, timeout, interrupted-stream, and backend-error states from the UI without additional tooling. In automated tests, explicit handler overrides remain cleaner and more precise.

**Alternatives considered**:

- **Only test-time overrides, no manual scenario controls** — rejected because the quickstart/manual acceptance flow would be much weaker.
- **Separate mock pages or debug toggles in the UI** — rejected because that would leak test scaffolding into the product surface.
- **Stateless success-only mock data** — rejected because it would not satisfy FR-039 for error and low-confidence handling.

---

## R9 — Backend conversation gap handling

**Decision**: Treat conversation CRUD, conversation-id creation, and persisted assistant metadata as explicit backend addenda rather than assuming they already exist.

**Rationale**: The spec lists these as assumptions, but the checked-in backend currently exposes only `/ask-question`, `/health`, `/evaluate`, and `/analytics`. The DB tables and repository helpers exist, which means the addenda are feasible, but the actual FastAPI routes are not yet wired. The frontend therefore needs a contract that clearly separates “required for real backend” from “mock-mode available now”.

**Alternatives considered**:

- **Assume the routes exist and plan against them as if shipped** — rejected because it would produce a plan disconnected from repo reality.
- **Fold backend implementation into this frontend feature** — rejected because the spec explicitly scopes backend changes out and the frontend should treat the backend as an external contract.

---

## Open follow-ups (for later features, not this one)

- Revisit transcript virtualization only if real-world message counts or profiling show the 100-message target is insufficient.
- Revisit syntax highlighting if interview/demo feedback says plain formatted code blocks are inadequate.
- Revisit a richer component primitive library only if multiple subsequent features need shared dialog/popover primitives.
