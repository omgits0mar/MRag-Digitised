# Quickstart: Chat UI Core

**Branch**: `006-chat-ui-core` | **Plan**: `plan.md`

This quickstart verifies the completed Feature 006 in both mock mode and, when backend addenda are available, against the real FastAPI service.

---

## 0. Prerequisites

- The repository `mrag` conda environment is available locally.
- Node/npm come from that environment.
- Commands are run from the repository root unless noted.

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

Expected: installation succeeds and the chat UI dependencies (`react-markdown`, `remark-gfm`,
`unist-util-visit`) resolve cleanly.

---

## 2. Run the app in mock mode

Ensure `frontend/.env` contains:

```bash
VITE_ENABLE_MOCK=true
VITE_ENABLE_STREAMING=true
```

Then start the dev server:

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

Expected:

- The shell loads.
- The Chat route renders the real chat workspace instead of the placeholder.
- The conversation list/history surfaces are visible and keyboard-focusable.
- The header and sidebar both expose a `New chat` action.

---

## 3. Happy-path chat verification

In mock mode, submit a normal question such as:

```text
What are the main stages of the MRAG pipeline?
```

Expected:

- Your question appears immediately as a user message.
- An assistant placeholder enters a visible thinking state.
- The answer begins streaming into the assistant message.
- Markdown content renders as formatted text, not literal markdown syntax.
- The newest assistant message becomes the active source-panel target.
- Citation markers activate the matching source card.
- Token/latency metadata renders only when present.

Also verify:

- `Shift+Enter` inserts a newline.
- Scrolling upward reveals a “jump to latest” affordance instead of stealing scroll.
- The mobile layout (≤768px) keeps the input usable while the source panel is open.

---

## 4. Mock scenario verification

The mock handlers support scenario tags in the submitted question text:

```text
[mock:fallback] explain why the answer is uncertain
[mock:error] trigger backend failure handling
[mock:timeout] trigger timeout handling
[mock:interrupt] trigger a partial stream and interruption
```

Expected results:

- `[mock:fallback]` renders a completed assistant message with low-confidence/fallback treatment and the explicit “no sources” state.
- `[mock:error]` renders an inline assistant error state with Retry.
- `[mock:timeout]` renders a timeout-specific inline error.
- `[mock:interrupt]` preserves partial content, marks the message interrupted, and offers Retry.

For each case, verify that a subsequent normal question still succeeds.

---

## 5. Conversation management verification

1. Ask a first question and allow it to complete.
2. Start a new chat from the header or sidebar.
3. Ask a second question.
4. Switch between the saved conversations from the conversation list or History page.
5. Delete one conversation and confirm the explicit cancel path works.

Expected:

- The list shows title, timestamp, and message count.
- Switching conversations replaces the full transcript without leaking streaming state.
- Deleting the active conversation returns the UI to the welcome/empty state.
- Starting a new chat from the header or sidebar clears the active transcript without deleting prior history.

---

## 6. Automated checks

Run the frontend quality gates:

```bash
cd frontend
npm run test
npm run lint
npm run typecheck
npm run build
npm run build:check
```

Expected:

- Chat integration and unit tests pass in mock mode.
- Accessibility checks report zero critical violations for the required chat states.
- Production build succeeds and excludes mock artifacts, as in Feature 005.
- The key feature-focused specs include `tests/integration/test_chat_page.tsx`,
  `tests/integration/test_streaming_flow.tsx`, and `tests/integration/test_history_page.tsx`.

---

## 7. Real-backend verification

Only perform this step if the backend addenda from `contracts/chat_api.md` have landed.

Start the backend:

```bash
conda activate mrag
uvicorn src.mrag.api.app:app --reload --port 8000
```

Update `frontend/.env`:

```bash
VITE_ENABLE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_STREAMING=true
```

Restart `npm run dev`.

Expected:

- If `POST /ask-question/stream` exists, the chat streams normally.
- If streaming is absent but `POST /ask-question` works, the UI falls back to one-shot responses without breaking the transcript.
- If conversation CRUD is absent, the chat still works for the active session, but conversation list/detail/delete paths should be considered backend-blocked rather than frontend-broken.

---

## 8. Troubleshooting

- **Streaming never starts in mock mode**: verify `VITE_ENABLE_STREAMING=true` and check that the question did not trigger a non-stream scenario override.
- **The source panel is empty for normal mock answers**: confirm the focused message is an assistant message and not a previous user prompt.
- **Retry does nothing**: inspect whether the last assistant message is in a terminal error/interrupted/cancelled state; retry is intentionally unavailable for completed messages.
- **Real backend works for ask but not conversations**: the backend addenda for conversation routes likely have not shipped yet; continue validating those flows in mock mode.
