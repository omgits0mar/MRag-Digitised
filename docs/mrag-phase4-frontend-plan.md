# MRAG Project — Phase 4: Frontend & Chat UI Extension

**Project:** Multilingual RAG Platform (MRAG)
**Constitution Version:** 1.0.0
**Created:** 2026-04-12
**Status:** Planning
**PM:** Project Manager
**Extends:** mrag-project-plan.md (Phase 0–3)

---

## Updated Project Directory Structure (additions only)

```
.specify/
├── specs/
│   ├── ... (existing 000–009)
│   ├── 010-frontend-foundation/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   ├── 011-chat-ui-core/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   └── 012-advanced-chat-features/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md

mrag/
├── ... (existing backend)
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── public/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   ├── client.ts           # Axios/fetch wrapper for backend API
│   │   │   ├── endpoints.ts        # Typed endpoint definitions
│   │   │   └── types.ts            # Shared API response types
│   │   ├── stores/
│   │   │   ├── chatStore.ts        # Zustand store for chat state
│   │   │   ├── conversationStore.ts# Conversation history state
│   │   │   └── settingsStore.ts    # Model selection, preferences
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppShell.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Header.tsx
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── InputBar.tsx
│   │   │   │   ├── TypingIndicator.tsx
│   │   │   │   └── StreamRenderer.tsx
│   │   │   ├── references/
│   │   │   │   ├── SourcePanel.tsx
│   │   │   │   ├── ChunkCard.tsx
│   │   │   │   └── RelevanceBar.tsx
│   │   │   ├── conversations/
│   │   │   │   ├── ConversationList.tsx
│   │   │   │   ├── ConversationItem.tsx
│   │   │   │   └── SearchConversations.tsx
│   │   │   ├── settings/
│   │   │   │   ├── ModelSelector.tsx
│   │   │   │   ├── RetrievalConfig.tsx
│   │   │   │   └── PreferencesPanel.tsx
│   │   │   └── metrics/
│   │   │       ├── TokenCounter.tsx
│   │   │       ├── LatencyBadge.tsx
│   │   │       └── UsageDashboard.tsx
│   │   ├── hooks/
│   │   │   ├── useChat.ts
│   │   │   ├── useConversations.ts
│   │   │   ├── useStreaming.ts
│   │   │   └── useTokenCount.ts
│   │   ├── pages/
│   │   │   ├── ChatPage.tsx
│   │   │   ├── HistoryPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   ├── styles/
│   │   │   └── globals.css
│   │   └── utils/
│   │       ├── formatters.ts
│   │       ├── tokenEstimator.ts
│   │       └── markdownRenderer.ts
│   └── tests/
│       ├── components/
│       ├── hooks/
│       ├── stores/
│       └── e2e/
```

---

## Updated Feature Dependency Map

```
000-project-foundation (Phase 0)
    │
    ├── 001 → 002 → 003 (Phase 1)
    │                 │
    │                 ├── 004 → 005 → 006 (Phase 2)
    │                 │
    │                 ├── 007 → 008 (Phase 3)
    │                 │     │
    │                 │     └── 010-frontend-foundation (Phase 4)
    │                 │           │
    │                 │           ├── 011-chat-ui-core (Phase 4)
    │                 │           │     │
    │                 │           │     └── 012-advanced-chat-features (Phase 4)
    │                 │           │
    │                 │           └─────────────────────────────────────
    │                 │
    │                 └── 009 (Phase 3)
```

---

## Phase 4 Technical Context (frontend-specific)

| Field                | Value                                                           |
| -------------------- | --------------------------------------------------------------- |
| Language/Version     | TypeScript 5.x, React 18+                                      |
| Build Tool           | Vite 5+                                                         |
| UI Framework         | React + Tailwind CSS + shadcn/ui                                |
| State Management     | Zustand                                                         |
| HTTP Client          | Axios (with interceptors for auth/error handling)               |
| Markdown Rendering   | react-markdown + rehype-highlight                               |
| Testing              | Vitest + React Testing Library + Playwright (e2e)               |
| Bundling Target      | Modern browsers (ES2020+)                                       |
| API Integration      | Consumes FastAPI endpoints from Feature 007/008                 |
| Streaming            | Server-Sent Events (SSE) or WebSocket for LLM streaming        |
| Performance Goals    | <100ms first input delay, <3s largest contentful paint          |
| Constraints          | Must work without backend for dev (mock mode), responsive ≥360px|

---

---

# FEATURE 010 — Frontend Foundation & Dev Environment

---

## 010 / spec.md

**Feature Branch:** 010-frontend-foundation
**Created:** 2026-04-12
**Status:** Draft
**Depends on:** 007-fastapi-integration, 008-database-integration

### Overview

Set up the frontend project scaffold, development environment, API client layer, state management foundation, and application shell that all subsequent frontend features depend on. This mirrors the role of Feature 000 for the backend.

### User Stories

**US-010-1: As a frontend developer, I want a standardized React project with TypeScript, linting, and hot-reload so that I can develop UI features productively.**

- GIVEN a freshly cloned repository
- WHEN I run the frontend setup command
- THEN all dependencies install, the dev server starts, and hot-reload works
- Independent Test: `cd frontend && npm install && npm run dev` serves the app at localhost

**US-010-2: As a frontend developer, I want a typed API client layer so that all backend calls are type-safe and centralized.**

- GIVEN a backend endpoint (e.g., POST /ask-question)
- WHEN any component needs to call it
- THEN it uses the typed API client, which handles errors, retries, and auth headers consistently
- Independent Test: Call the `/health` endpoint via the client, verify typed response

**US-010-3: As a frontend developer, I want a global state management system so that chat state, conversations, and settings are shared across components without prop-drilling.**

- GIVEN chat messages, conversation list, and user preferences
- WHEN any component reads or writes state
- THEN it uses Zustand stores with typed selectors and actions
- Independent Test: Dispatch an action, verify state update in a different component

**US-010-4: As a user, I want a responsive application shell with sidebar navigation so that I can switch between chat, history, and settings views.**

- GIVEN the application loads
- WHEN I interact with the layout
- THEN I see a sidebar with navigation (Chat, History, Settings), a header with branding, and a main content area
- GIVEN a mobile viewport (≤768px)
- WHEN the layout renders
- THEN the sidebar collapses into a hamburger menu
- Independent Test: Resize the browser, verify sidebar collapses/expands

### Assumptions & Dependencies

- Backend API (Feature 007) is deployed or a mock server is available
- Node.js 18+ and npm are available on all development machines
- CORS is configured on the backend to accept frontend origin

### Success Criteria

- `npm run build` produces zero errors and zero TypeScript warnings
- API client handles 4xx/5xx with user-facing error messages
- Zustand stores are fully typed with no `any` types
- Application shell renders correctly from 360px to 2560px width
- Lighthouse performance score ≥ 85 on empty shell

### Constitution Compliance

- Article I: Frontend is a separate module with a clear interface to backend via API
- Article IX: TypeScript strict mode, ESLint, Prettier configured
- Article IX: Environment variables for API base URL, feature flags

---

## 010 / plan.md

**Branch:** 010-frontend-foundation | **Date:** 2026-04-12 | **Spec:** specs/010-frontend-foundation/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

Scaffold a Vite + React + TypeScript project inside `frontend/`. Use Tailwind CSS with shadcn/ui for component primitives (consistent design tokens, accessible components out of the box). State management via Zustand (lightweight, TypeScript-first, no boilerplate). API layer uses Axios with typed interceptors.

### Tech Stack Decisions

| Component         | Choice                     | Rationale                                                  |
| ----------------- | -------------------------- | ---------------------------------------------------------- |
| Build tool        | Vite 5                     | Fast HMR, native ESM, zero-config TypeScript               |
| UI framework      | React 18                   | Ecosystem, hooks, concurrent features                      |
| Type system       | TypeScript 5 (strict)      | Catches API contract drift at compile time                 |
| Styling           | Tailwind CSS + shadcn/ui   | Utility-first, accessible primitives, no runtime CSS-in-JS |
| State management  | Zustand                    | Minimal API, TypeScript-native, no context hell            |
| HTTP client       | Axios                      | Interceptors for auth/errors, request cancellation         |
| Routing           | React Router v6            | Standard, lazy-loading support                             |
| Markdown          | react-markdown + rehype    | Renders LLM output with syntax highlighting                |
| Testing           | Vitest + RTL               | Vite-native, fast, React Testing Library patterns          |
| E2E testing       | Playwright                 | Cross-browser, reliable, good DX                           |
| Mock server       | MSW (Mock Service Worker)  | Intercepts network in dev/test without mock backends       |

### API Client Architecture

```
src/api/
├── client.ts        → Axios instance with baseURL, interceptors, error normalization
├── endpoints.ts     → Typed functions: askQuestion(), getHealth(), getConversations(), etc.
└── types.ts         → Interfaces mirroring backend Pydantic schemas:
                        QuestionRequest, QuestionResponse, HealthResponse,
                        ConversationSummary, ConversationDetail, MessageRecord,
                        TokenUsage, RetrievalSource
```

### State Architecture

```
stores/
├── chatStore.ts         → messages[], isStreaming, currentConversationId, sendMessage()
├── conversationStore.ts → conversations[], activeId, loadConversations(), deleteConversation()
└── settingsStore.ts     → selectedModel, topK, scoreThreshold, temperature, persist to localStorage
```

---

## 010 / tasks.md

**Input:** specs/010-frontend-foundation/
**Prerequisites:** 007-fastapi-integration, 008-database-integration complete (or mock server available)

### Phase 4 — US-010-1: Project Scaffold

- **T010-01** [P] — Initialize Vite + React + TypeScript project in `frontend/`
  - Files: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/index.html`
  - Done: `npm install && npm run dev` starts dev server, `npm run build` succeeds with zero errors

- **T010-02** [P] — Configure Tailwind CSS, shadcn/ui, ESLint, Prettier
  - Files: `frontend/tailwind.config.ts`, `frontend/postcss.config.js`, `frontend/.eslintrc.cjs`, `frontend/.prettierrc`
  - Done: Tailwind classes render, shadcn/ui components importable, `npm run lint` passes

- **T010-03** [P] — Create `.env.example` and environment configuration for frontend
  - Files: `frontend/.env.example`, `frontend/src/config.ts`
  - Done: `VITE_API_BASE_URL`, `VITE_ENABLE_STREAMING`, `VITE_DEFAULT_MODEL` documented and typed

- **T010-04** — Set up React Router with lazy-loaded pages
  - Files: `frontend/src/App.tsx`, `frontend/src/pages/ChatPage.tsx`, `frontend/src/pages/HistoryPage.tsx`, `frontend/src/pages/SettingsPage.tsx`
  - Done: Routes `/`, `/history`, `/settings` render placeholder pages, code-splitting verified in build

### Phase 4 — US-010-2: API Client Layer

- **T010-05** — Create `src/api/types.ts` with all backend API types mirroring Pydantic schemas
  - File: `frontend/src/api/types.ts`
  - Done: Interfaces for every request/response from Features 007/008: `QuestionRequest`, `QuestionResponse`, `HealthResponse`, `ConversationSummary`, `ConversationDetail`, `MessageRecord`, `RetrievalSource`, `TokenUsage`, `EvaluateRequest`, `EvaluateResponse`, `ErrorResponse`

- **T010-06** — Create `src/api/client.ts` with Axios instance and interceptors
  - File: `frontend/src/api/client.ts`
  - Done: Base URL from env, request/response interceptors, error normalization to `ApiError` type, request cancellation support

- **T010-07** — Create `src/api/endpoints.ts` with typed endpoint functions
  - File: `frontend/src/api/endpoints.ts`
  - Done: `askQuestion()`, `getHealth()`, `getConversations()`, `getConversation(id)`, `deleteConversation(id)`, `getAnalytics()`, `runEvaluation()` all typed

- **T010-08** — Create MSW mock handlers for all endpoints
  - Files: `frontend/src/mocks/handlers.ts`, `frontend/src/mocks/browser.ts`, `frontend/src/mocks/data.ts`
  - Done: All endpoints mocked with realistic sample data, dev server works without backend

### Phase 4 — US-010-3: State Management

- **T010-09** — Create `src/stores/chatStore.ts` with Zustand
  - File: `frontend/src/stores/chatStore.ts`
  - Done: `messages`, `isStreaming`, `error`, `sendMessage()`, `clearChat()`, `setConversation()` actions typed

- **T010-10** — Create `src/stores/conversationStore.ts` with Zustand
  - File: `frontend/src/stores/conversationStore.ts`
  - Done: `conversations`, `activeId`, `loadConversations()`, `createConversation()`, `deleteConversation()` with API integration

- **T010-11** — Create `src/stores/settingsStore.ts` with Zustand + localStorage persistence
  - File: `frontend/src/stores/settingsStore.ts`
  - Done: `selectedModel`, `topK`, `scoreThreshold`, `temperature`, `theme` persisted to localStorage, typed selectors

### Phase 4 — US-010-4: Application Shell

- **T010-12** — Create `src/components/layout/AppShell.tsx` with responsive layout
  - File: `frontend/src/components/layout/AppShell.tsx`
  - Done: Sidebar + header + main content area, responsive collapse at 768px breakpoint

- **T010-13** — Create `src/components/layout/Sidebar.tsx` with navigation
  - File: `frontend/src/components/layout/Sidebar.tsx`
  - Done: Navigation links (Chat, History, Settings), active state highlighting, "New Chat" button, collapsible on mobile

- **T010-14** — Create `src/components/layout/Header.tsx` with branding and controls
  - File: `frontend/src/components/layout/Header.tsx`
  - Done: App title/logo, mobile hamburger toggle, model selector dropdown in header

- **T010-15** — Create unit tests for API client, stores, and layout components
  - Files: `frontend/tests/api/test_client.ts`, `frontend/tests/stores/test_chatStore.ts`, `frontend/tests/components/test_AppShell.tsx`
  - Done: API client error handling tested, store actions produce correct state, layout renders at multiple breakpoints

### Checkpoint: `npm run build && npm run test && npm run lint` passes. App shell renders. API client connects to backend or mock. All stores typed.

---

---

# FEATURE 011 — Chat UI Core

---

## 011 / spec.md

**Feature Branch:** 011-chat-ui-core
**Created:** 2026-04-12
**Status:** Draft
**Depends on:** 010-frontend-foundation

### Overview

Build the primary chat interface: message input, message display with markdown rendering, real-time streaming from the LLM, conversation threading, and the retrieval source reference panel.

### User Stories

**US-011-1: As a user, I want to type a question and see the AI's answer rendered in a chat interface so that I have a familiar conversational experience.**

- GIVEN the chat page is open
- WHEN I type a question and press Enter (or click Send)
- THEN my question appears as a "user" bubble, a loading indicator shows, and the AI response appears as an "assistant" bubble with markdown rendering (headings, code blocks, lists, bold/italic)
- GIVEN the AI is generating a response
- WHEN the response is being streamed
- THEN tokens appear incrementally in the assistant bubble (typewriter effect)
- Independent Test: Send a question, verify both bubbles render, markdown formats correctly

**US-011-2: As a user, I want to see which source documents and chunks the AI used to generate its answer so that I can verify the information and explore further.**

- GIVEN an AI response that was generated from retrieved context
- WHEN I look at the response
- THEN I see numbered citation markers [1], [2], [3] inline in the answer text
- WHEN I click a citation marker or open the "Sources" panel
- THEN I see: chunk text, relevance score (as a percentage bar), source document ID, question type, domain tag, and chunk index within the original document
- GIVEN a response with no retrieved context (fallback answer)
- WHEN I view the response
- THEN no citation markers appear, and the Sources panel says "No sources used for this response"
- Independent Test: Send a factual question, verify citation markers appear and source panel populates

**US-011-3: As a user, I want to see token usage and latency for each message so that I can understand the system's performance and cost.**

- GIVEN an AI response is returned
- WHEN I view the message metadata
- THEN I see: prompt tokens, completion tokens, total tokens, retrieval latency (ms), generation latency (ms), total response time (ms), and cache hit indicator
- GIVEN I want a quick glance
- WHEN the response renders
- THEN a subtle metadata footer appears below the message with token count and timing
- WHEN I click the metadata footer
- THEN a detailed breakdown popover appears
- Independent Test: Send a question, verify token counts and latency values are displayed

**US-011-4: As a user, I want to start new conversations and switch between existing ones so that I can organize my queries by topic.**

- GIVEN I have existing conversations
- WHEN I open the sidebar
- THEN I see a list of past conversations with title (auto-generated from first message), timestamp, and message count
- WHEN I click "New Chat"
- THEN the current conversation is saved and a fresh chat opens
- WHEN I click an existing conversation
- THEN the chat window loads that conversation's full message history
- Independent Test: Create two conversations, switch between them, verify messages are preserved

**US-011-5: As a user, I want the chat to handle errors gracefully so that I'm never left wondering what went wrong.**

- GIVEN a network error occurs during a request
- WHEN the request fails
- THEN an error message appears in the chat (not a blank screen or console error), with a "Retry" button
- GIVEN the backend returns a fallback/low-confidence response
- WHEN the response renders
- THEN a visual indicator (amber badge) shows this is a low-confidence answer
- Independent Test: Disconnect network, send a question, verify error UI appears with retry

### Assumptions & Dependencies

- Backend supports SSE or WebSocket for streaming responses (or frontend polls; streaming preferred)
- Backend response includes `sources` array, `token_usage` object, and `latency_ms` fields
- Conversation CRUD endpoints exist (from Feature 008)

### Success Criteria

- Message round-trip (type → send → display response) completes in <3s for cached queries
- Markdown renders correctly including code blocks with syntax highlighting
- Citation markers link to correct source chunks
- Token counts match backend-reported values
- Conversation switching preserves scroll position
- Error states never show a blank screen

### Constitution Compliance

- Article VII: Consumes API contracts from Feature 007 exactly
- Article V: Displays confidence/fallback state from generation pipeline
- Article VIII: Displays cache hit indicator from Feature 006
- Article I: UI components are modular and independently testable

---

## 011 / plan.md

**Branch:** 011-chat-ui-core | **Date:** 2026-04-12 | **Spec:** specs/011-chat-ui-core/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

Build a message-oriented chat UI. Each message is a `ChatMessage` object containing the question, response, sources, token usage, and timing metadata. Streaming uses Server-Sent Events (SSE) via the `EventSource` API or a fetch-based ReadableStream. Markdown rendering with `react-markdown` + `rehype-highlight` for code blocks. The source reference panel is a collapsible right-side drawer.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  AppShell                                               │
│ ┌──────────┐ ┌────────────────────────┐ ┌────────────┐ │
│ │ Sidebar   │ │     ChatWindow         │ │ SourcePanel│ │
│ │           │ │  ┌──────────────────┐  │ │            │ │
│ │ Conv List │ │  │  MessageBubble   │  │ │ ChunkCard  │ │
│ │           │ │  │  (user)          │  │ │ ChunkCard  │ │
│ │ New Chat  │ │  │  MessageBubble   │  │ │ ChunkCard  │ │
│ │           │ │  │  (assistant)     │  │ │            │ │
│ │ Search    │ │  │  ┌─ citations ─┐ │  │ │ Relevance  │ │
│ │           │ │  │  │ [1] [2] [3] │ │  │ │ Score Bar  │ │
│ │           │ │  │  └─────────────┘ │  │ │            │ │
│ │           │ │  │  ┌─ metadata  ─┐ │  │ │            │ │
│ │           │ │  │  │ 142 tokens  │ │  │ │            │ │
│ │           │ │  │  │ 1.2s        │ │  │ │            │ │
│ │           │ │  │  └─────────────┘ │  │ │            │ │
│ │           │ │  └──────────────────┘  │ │            │ │
│ │           │ │  ┌──────────────────┐  │ │            │ │
│ │           │ │  │    InputBar      │  │ │            │ │
│ │           │ │  │  [____________▶] │  │ │            │ │
│ │           │ │  └──────────────────┘  │ │            │ │
│ └──────────┘ └────────────────────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Key Technical Decisions

| Decision               | Choice                                           | Rationale                                              |
| ---------------------- | ------------------------------------------------ | ------------------------------------------------------ |
| Streaming approach     | SSE via fetch + ReadableStream                   | Works with FastAPI StreamingResponse, no WS overhead   |
| Markdown rendering     | react-markdown + rehype-highlight + remark-gfm   | Handles code, tables, GFM; syntax highlighting built-in|
| Citation parsing       | Custom remark plugin to detect `[N]` patterns    | Links inline citations to source panel entries          |
| Source panel layout    | Collapsible right drawer (resizable)             | Doesn't obscure chat, accessible on demand             |
| Token display          | Inline footer (compact) + popover (detailed)     | Non-intrusive but accessible                           |
| Message virtualization | @tanstack/react-virtual for long conversations   | Prevents DOM bloat on 100+ message conversations       |
| Auto-scroll            | Scroll-to-bottom with "New messages" indicator   | Standard chat UX pattern                               |
| Conversation titles    | Auto-generated from first user message (truncated)| No manual naming required                              |

### Data Models (Frontend)

```typescript
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;                    // markdown text
  timestamp: string;                  // ISO 8601
  conversationId: string;
  sources?: RetrievalSource[];        // populated for assistant messages
  tokenUsage?: TokenUsage;
  latency?: LatencyBreakdown;
  confidence?: number;                // 0–1, from backend validator
  isFallback?: boolean;               // true if low-confidence fallback
  isStreaming?: boolean;              // true while tokens are arriving
  error?: string;                     // error message if request failed
}

interface RetrievalSource {
  chunkId: string;
  chunkText: string;
  relevanceScore: number;             // 0–1
  docId: string;
  questionType: string;               // factoid | descriptive | list | yes_no
  domain: string;                     // science | history | ...
  chunkIndex: number;
  totalChunks: number;
  originalQuestion?: string;
  originalAnswer?: string;
}

interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

interface LatencyBreakdown {
  embeddingMs: number;
  searchMs: number;
  llmMs: number;
  totalMs: number;
  cacheHit: boolean;
}
```

### Backend API Extensions Required

The backend (Feature 007/008) response schema needs to include these fields in `QuestionResponse`:

```python
class QuestionResponse(BaseModel):
    answer: str
    confidence_score: float
    sources: List[RetrievalSourceSchema]
    token_usage: TokenUsageSchema
    latency: LatencySchema
    conversation_id: str
    is_fallback: bool
```

If these fields don't exist yet, a backend task should be added to Feature 007/008 to include them.

---

## 011 / tasks.md

**Input:** specs/011-chat-ui-core/
**Prerequisites:** 010-frontend-foundation complete

### Phase 4 — US-011-1: Chat Window & Message Display

- **T011-01** — Create `src/components/chat/MessageBubble.tsx` with markdown rendering
  - File: `frontend/src/components/chat/MessageBubble.tsx`
  - Done: Renders user/assistant bubbles with different styling, markdown content via react-markdown, code block syntax highlighting, avatar indicators, timestamp

- **T011-02** — Create `src/components/chat/InputBar.tsx` with send functionality
  - File: `frontend/src/components/chat/InputBar.tsx`
  - Done: Text area with auto-resize, Send button, Enter to send / Shift+Enter for newline, disabled state while streaming, character count indicator

- **T011-03** — Create `src/components/chat/ChatWindow.tsx` composing messages + input
  - File: `frontend/src/components/chat/ChatWindow.tsx`
  - Done: Scrollable message list, auto-scroll to bottom on new messages, "New messages" indicator if scrolled up, empty state with welcome message

- **T011-04** — Create `src/components/chat/TypingIndicator.tsx`
  - File: `frontend/src/components/chat/TypingIndicator.tsx`
  - Done: Animated dots indicator while waiting for first token

- **T011-05** — Create `src/hooks/useStreaming.ts` for SSE/streaming response handling
  - File: `frontend/src/hooks/useStreaming.ts`
  - Done: Connects to SSE endpoint, incrementally appends tokens to message, handles stream close/error, returns `{ startStream, stopStream, isStreaming }`. Falls back to non-streaming fetch if SSE not available

- **T011-06** — Create `src/components/chat/StreamRenderer.tsx` for incremental token display
  - File: `frontend/src/components/chat/StreamRenderer.tsx`
  - Done: Receives streaming text, renders markdown progressively, cursor blink at end of stream

### Phase 4 — US-011-2: Source References & Citations

- **T011-07** — Create `src/components/references/SourcePanel.tsx` collapsible drawer
  - File: `frontend/src/components/references/SourcePanel.tsx`
  - Done: Right-side drawer, toggleable, lists sources for the selected message, "No sources" state for fallback messages

- **T011-08** — Create `src/components/references/ChunkCard.tsx` for individual source display
  - File: `frontend/src/components/references/ChunkCard.tsx`
  - Done: Displays chunk text (truncated with expand), relevance score bar, domain tag, doc ID, chunk index/total, collapsible full text

- **T011-09** — Create `src/components/references/RelevanceBar.tsx` visual score indicator
  - File: `frontend/src/components/references/RelevanceBar.tsx`
  - Done: Horizontal bar colored green (>0.7) / amber (0.4–0.7) / red (<0.4), percentage label

- **T011-10** — Create citation parsing logic to link `[N]` markers to source panel
  - File: `frontend/src/utils/citationParser.ts`
  - Done: Parses `[1]`, `[2]`, etc. in markdown, renders as clickable badges, clicking scrolls source panel to corresponding ChunkCard

### Phase 4 — US-011-3: Token Usage & Latency Display

- **T011-11** — Create `src/components/metrics/TokenCounter.tsx` inline message footer
  - File: `frontend/src/components/metrics/TokenCounter.tsx`
  - Done: Compact display: "142 tokens · 1.2s · ⚡ cached", click to expand detailed popover

- **T011-12** — Create `src/components/metrics/LatencyBadge.tsx` with detailed breakdown
  - File: `frontend/src/components/metrics/LatencyBadge.tsx`
  - Done: Popover showing: embed time, search time, LLM time, total time, cache hit/miss badge

- **T011-13** — Create `src/hooks/useTokenCount.ts` for client-side token estimation
  - File: `frontend/src/hooks/useTokenCount.ts`
  - Done: Estimates token count for input text using simple tokenizer (GPT-style ≈ 4 chars/token), shows live count while typing, warns when approaching limits

### Phase 4 — US-011-4: Conversation Management

- **T011-14** — Create `src/components/conversations/ConversationList.tsx`
  - File: `frontend/src/components/conversations/ConversationList.tsx`
  - Done: Lists conversations from store, auto-generated titles, timestamps, message counts, active conversation highlighted

- **T011-15** — Create `src/components/conversations/ConversationItem.tsx`
  - File: `frontend/src/components/conversations/ConversationItem.tsx`
  - Done: Single conversation entry with title, preview of last message, date, delete button with confirmation

- **T011-16** — Create `src/components/conversations/SearchConversations.tsx`
  - File: `frontend/src/components/conversations/SearchConversations.tsx`
  - Done: Search input filters conversation list by title/content, debounced (300ms)

- **T011-17** — Create `src/hooks/useConversations.ts` integrating store + API
  - File: `frontend/src/hooks/useConversations.ts`
  - Done: `loadConversations()`, `switchConversation(id)`, `createNew()`, `deleteConversation(id)` with optimistic updates

### Phase 4 — US-011-5: Error Handling & Low-Confidence States

- **T011-18** — Create error display within chat (inline error messages + retry)
  - File: Update `frontend/src/components/chat/MessageBubble.tsx`, create `frontend/src/components/chat/ErrorMessage.tsx`
  - Done: Network errors show inline error bubble with "Retry" button, retry re-sends the last user message

- **T011-19** — Create low-confidence / fallback visual indicators
  - File: Update `frontend/src/components/chat/MessageBubble.tsx`
  - Done: Fallback responses have amber left border + "Low confidence" badge, tooltip explains why

- **T011-20** — Create unit and integration tests for chat components
  - Files: `frontend/tests/components/test_ChatWindow.tsx`, `frontend/tests/components/test_MessageBubble.tsx`, `frontend/tests/components/test_SourcePanel.tsx`, `frontend/tests/hooks/test_useStreaming.ts`
  - Done: Markdown renders correctly, citations link to sources, token counts display, error states render, streaming mock works

### Checkpoint: Full chat UI operational. Messages send/receive. Sources display with citations. Token usage visible. Conversations switchable. Errors handled gracefully.

---

---

# FEATURE 012 — Advanced Chat Features & Settings

---

## 012 / spec.md

**Feature Branch:** 012-advanced-chat-features
**Created:** 2026-04-12
**Status:** Draft
**Depends on:** 011-chat-ui-core

### Overview

Add advanced user-facing features: model selection and configuration, retrieval parameter tuning, conversation export, theme switching, keyboard shortcuts, usage analytics dashboard, and end-to-end tests.

### User Stories

**US-012-1: As a user, I want to select which LLM model is used for generating answers so that I can choose between speed, quality, or cost tradeoffs.**

- GIVEN the settings page or the header model selector
- WHEN I select a different model (e.g., "llama-3-70b" vs "mixtral-8x7b")
- THEN subsequent queries use the selected model, and the model name is visible in the message metadata
- Independent Test: Switch models, send queries, verify model name in response metadata differs

**US-012-2: As a power user, I want to tune retrieval parameters (top-K, score threshold, temperature) so that I can control answer quality and diversity.**

- GIVEN the settings page
- WHEN I adjust top_k (slider 1–20), score_threshold (slider 0–1), or temperature (slider 0–2)
- THEN subsequent queries use the updated parameters
- WHEN I reset to defaults
- THEN all parameters return to their default values
- Independent Test: Set top_k=1, send a question, verify only 1 source is returned

**US-012-3: As a user, I want to export a conversation so that I can save it for reference or share it.**

- GIVEN a conversation with multiple messages
- WHEN I click "Export"
- THEN I can download the conversation as Markdown (.md) or JSON (.json)
- The exported file includes all messages, sources, token usage, and timestamps
- Independent Test: Export a 5-message conversation, open the file, verify content completeness

**US-012-4: As a user, I want to switch between light and dark themes so that I can use the app comfortably in different lighting conditions.**

- GIVEN the settings or header theme toggle
- WHEN I switch themes
- THEN the entire UI updates to the selected theme, and the preference persists across sessions
- Independent Test: Switch to dark mode, reload, verify dark mode persists

**US-012-5: As a user, I want keyboard shortcuts so that I can navigate the app efficiently.**

- GIVEN the app is open
- WHEN I press Ctrl+N (or Cmd+N on Mac)
- THEN a new conversation starts
- WHEN I press Ctrl+/ (or Cmd+/)
- THEN the keyboard shortcuts help modal opens
- Independent Test: Press shortcut, verify expected action occurs

**US-012-6: As a system operator, I want a usage analytics dashboard so that I can see query volumes, model usage, average latencies, and token consumption at a glance.**

- GIVEN analytics data accumulated via Feature 008
- WHEN I navigate to the dashboard (or a tab within Settings)
- THEN I see charts: queries/day over last 30 days, average latency trend, token usage by model, cache hit rate, top domains queried
- Independent Test: Navigate to dashboard with mock data, verify all charts render

### Assumptions & Dependencies

- Backend supports a `model` parameter in `QuestionRequest` to select LLM
- Backend analytics endpoints return aggregated data (from Feature 008)
- Export is client-side (no backend endpoint needed)

### Success Criteria

- Model switching takes effect on the very next query
- Parameter changes persist across sessions via localStorage
- Exported conversations are valid Markdown/JSON, openable in any editor
- Theme switch is instant (<100ms repaint)
- Keyboard shortcuts don't conflict with browser defaults
- Dashboard charts load in <2 seconds with mock data

### Constitution Compliance

- Article V: Model selection abstraction allows swapping LLM providers
- Article VIII: Retrieval parameters map to Feature 006 caching config
- Article IX: User preferences persisted per Article IX secrets/config principles
- Article VI: Dashboard visualizes evaluation metrics from Feature 009

---

## 012 / plan.md

**Branch:** 012-advanced-chat-features | **Date:** 2026-04-12 | **Spec:** specs/012-advanced-chat-features/spec.md
**Constitution Version:** 1.0.0

### Technical Approach

Model selector uses a dropdown populated from a backend `/models` endpoint (or static config). Retrieval parameter sliders use shadcn/ui `Slider` components bound to the settings Zustand store. Export is fully client-side using `Blob` + `URL.createObjectURL()`. Theme uses Tailwind's `dark:` variant with a CSS class toggle on `<html>`. Keyboard shortcuts via `useHotkeys` hook (or a lightweight custom implementation). Analytics dashboard uses `recharts` for charts.

### Key Technical Decisions

| Decision              | Choice                          | Rationale                                          |
| --------------------- | ------------------------------- | -------------------------------------------------- |
| Model list source     | `/models` endpoint or config    | Allows backend to control available models          |
| Parameter persistence | Zustand + localStorage          | Survives page reload, no backend dependency         |
| Export format         | Client-side Blob generation     | No backend endpoint needed, instant download        |
| Theme implementation  | Tailwind `dark:` + class toggle | No runtime CSS, instant switch, SSR-compatible      |
| Keyboard shortcuts    | Custom `useHotkeys` hook        | Minimal dependency, full control over conflicts     |
| Dashboard charts      | recharts                        | React-native, composable, good TypeScript support   |

### Module Structure (additions)

```
src/components/settings/
├── ModelSelector.tsx          # Dropdown for model selection
├── RetrievalConfig.tsx        # Sliders for top_k, threshold, temperature
└── PreferencesPanel.tsx       # Theme toggle, export, shortcuts

src/components/metrics/
└── UsageDashboard.tsx         # Charts: queries/day, latency, tokens, cache

src/hooks/
├── useHotkeys.ts              # Keyboard shortcut handler
└── useExport.ts               # Conversation export logic

src/utils/
└── exportConversation.ts      # Markdown/JSON serialization
```

---

## 012 / tasks.md

**Input:** specs/012-advanced-chat-features/
**Prerequisites:** 011-chat-ui-core complete

### Phase 4 — US-012-1: Model Selection

- **T012-01** — Create `src/components/settings/ModelSelector.tsx`
  - File: `frontend/src/components/settings/ModelSelector.tsx`
  - Done: Dropdown lists available models, selected model saved to settingsStore, displayed in header and message metadata

- **T012-02** — Integrate model parameter into API requests
  - File: Update `frontend/src/api/endpoints.ts`, `frontend/src/stores/chatStore.ts`
  - Done: `askQuestion()` includes `model` field from settingsStore, responses show which model was used

### Phase 4 — US-012-2: Retrieval Parameter Tuning

- **T012-03** — Create `src/components/settings/RetrievalConfig.tsx`
  - File: `frontend/src/components/settings/RetrievalConfig.tsx`
  - Done: Sliders for `top_k` (1–20), `score_threshold` (0–1), `temperature` (0–2), "Reset Defaults" button, values bound to settingsStore

- **T012-04** — Integrate retrieval parameters into API requests
  - File: Update `frontend/src/api/endpoints.ts`
  - Done: `askQuestion()` includes `top_k`, `score_threshold`, `temperature` from settingsStore

### Phase 4 — US-012-3: Conversation Export

- **T012-05** — Create `src/utils/exportConversation.ts` with Markdown and JSON serializers
  - File: `frontend/src/utils/exportConversation.ts`
  - Done: `toMarkdown(messages)` and `toJSON(messages)` produce complete exports with sources, tokens, timestamps

- **T012-06** — Create `src/hooks/useExport.ts` and export button in conversation menu
  - File: `frontend/src/hooks/useExport.ts`, update `frontend/src/components/conversations/ConversationItem.tsx`
  - Done: "Export as Markdown" and "Export as JSON" options in conversation context menu, downloads file via Blob

### Phase 4 — US-012-4: Theme Switching

- **T012-07** — Implement dark/light theme toggle
  - Files: Update `frontend/src/styles/globals.css`, `frontend/src/stores/settingsStore.ts`, create `frontend/src/components/layout/ThemeToggle.tsx`
  - Done: Toggle in header switches `dark` class on `<html>`, persists to localStorage, respects system preference on first load

### Phase 4 — US-012-5: Keyboard Shortcuts

- **T012-08** — Create `src/hooks/useHotkeys.ts` and shortcuts help modal
  - Files: `frontend/src/hooks/useHotkeys.ts`, `frontend/src/components/layout/ShortcutsModal.tsx`
  - Done: Ctrl+N → new chat, Ctrl+/ → help modal, Escape → close panels, Ctrl+E → toggle source panel, shortcuts don't fire when typing in input

### Phase 4 — US-012-6: Usage Analytics Dashboard

- **T012-09** — Create `src/components/metrics/UsageDashboard.tsx` with recharts
  - File: `frontend/src/components/metrics/UsageDashboard.tsx`
  - Done: Line chart (queries/day), bar chart (tokens by model), area chart (avg latency trend), stat cards (total queries, cache hit rate, avg confidence)

- **T012-10** — Create API integration for analytics data
  - File: Update `frontend/src/api/endpoints.ts`
  - Done: `getAnalytics(dateRange)` fetches aggregated data from backend Feature 008 analytics endpoint

### Phase 4 — US-012-7: Settings Page Composition

- **T012-11** — Create `src/pages/SettingsPage.tsx` composing all settings panels
  - File: `frontend/src/pages/SettingsPage.tsx`
  - Done: Tabs or sections for: Model & Parameters, Appearance, Keyboard Shortcuts, Export, Analytics Dashboard

### Phase 4 — Testing

- **T012-12** — Create unit tests for all new components
  - Files: `frontend/tests/components/test_ModelSelector.tsx`, `frontend/tests/components/test_RetrievalConfig.tsx`, `frontend/tests/components/test_UsageDashboard.tsx`, `frontend/tests/utils/test_exportConversation.ts`
  - Done: Model selector changes state, sliders update store, export produces valid files, dashboard renders with mock data

- **T012-13** — Create end-to-end tests with Playwright
  - Files: `frontend/tests/e2e/chat-flow.spec.ts`, `frontend/tests/e2e/settings.spec.ts`, `frontend/tests/e2e/conversations.spec.ts`
  - Done: Full user journey: open app → send question → view sources → switch conversation → export → change settings → verify everything persists

### Checkpoint: End of Phase 4. Full Chat UI operational with model selection, parameter tuning, exports, themes, shortcuts, and analytics dashboard. E2E tests pass.

---

---

# BACKEND API EXTENSIONS (Addendum to Features 007/008)

To support the frontend, the following backend tasks should be added to existing features:

### Additions to Feature 007 — FastAPI Integration

- **T007-09** — Add SSE streaming endpoint `POST /ask-question/stream`
  - File: Update `src/mrag/api/routes/ask.py`
  - Done: Returns `StreamingResponse` with `text/event-stream` content type, sends tokens incrementally

- **T007-10** — Add `GET /models` endpoint listing available LLM models
  - File: Create `src/mrag/api/routes/models.py`
  - Done: Returns list of available models with name, provider, description, speed/quality tier

- **T007-11** — Extend `QuestionResponse` schema with `token_usage`, `latency`, `is_fallback` fields
  - File: Update `src/mrag/api/schemas.py`
  - Done: Response includes `TokenUsage`, `LatencyBreakdown`, `is_fallback`, `model_used` fields

- **T007-12** — Add CORS configuration for frontend origin
  - File: Update `src/mrag/api/middleware.py`
  - Done: CORS allows frontend origin (configurable via env), credentials supported

### Additions to Feature 008 — Database Integration

- **T008-07** — Add `GET /conversations` and `GET /conversations/{id}` endpoints
  - File: Create `src/mrag/api/routes/conversations.py`
  - Done: Lists conversations with summary, loads full conversation with all messages

- **T008-08** — Add `DELETE /conversations/{id}` endpoint
  - File: Update `src/mrag/api/routes/conversations.py`
  - Done: Soft-deletes conversation, returns 204

- **T008-09** — Add `GET /analytics` endpoint with aggregated metrics
  - File: Create `src/mrag/api/routes/analytics.py`
  - Done: Returns queries/day, avg latency, token usage by model, cache hit rate, top domains for date range

---

---

# UPDATED MASTER TASK SUMMARY

## Total: 13 Features, 119 Tasks

| Feature                            | Phase | Tasks                          | Dependencies | Status         |
| ---------------------------------- | ----- | ------------------------------ | ------------ | -------------- |
| 000 — Project Foundation           | 0     | T000-01 → T000-11 (11 tasks)  | None         | ⬜ Not Started  |
| 001 — Dataset Processing           | 1     | T001-01 → T001-10 (10 tasks)  | 000          | ⬜ Not Started  |
| 002 — Embedding & Vector Store     | 1     | T002-01 → T002-08 (8 tasks)   | 001          | ⬜ Not Started  |
| 003 — Basic Retrieval              | 1     | T003-01 → T003-06 (6 tasks)   | 002          | ⬜ Not Started  |
| 004 — Query Processing             | 2     | T004-01 → T004-08 (8 tasks)   | 003          | ⬜ Not Started  |
| 005 — Response Generation          | 2     | T005-01 → T005-10 (10 tasks)  | 003, 004     | ⬜ Not Started  |
| 006 — Caching & Performance        | 2     | T006-01 → T006-08 (8 tasks)   | 005          | ⬜ Not Started  |
| 007 — FastAPI Integration          | 3     | T007-01 → T007-12 (12 tasks)  | 006          | ⬜ Not Started  |
| 008 — Database Integration         | 3     | T008-01 → T008-09 (9 tasks)   | 007          | ⬜ Not Started  |
| 009 — Evaluation Framework         | 3     | T009-01 → T009-08 (8 tasks)   | 003, 005     | ⬜ Not Started  |
| **010 — Frontend Foundation**      | **4** | **T010-01 → T010-15 (15 tasks)** | **007, 008** | ⬜ Not Started  |
| **011 — Chat UI Core**             | **4** | **T011-01 → T011-20 (20 tasks)** | **010**      | ⬜ Not Started  |
| **012 — Advanced Chat Features**   | **4** | **T012-01 → T012-13 (13 tasks)** | **011**      | ⬜ Not Started  |

## Updated Parallel Execution Map

```
Phase 0:  [000 Foundation] ──────────────────────────────────────────────────
Phase 1:           ├── [001 Data] → [002 Embed] → [003 Retrieve] ───────────
Phase 2:                                              ├── [004 Query] ──────
                                                      │    └── [005 Gen]
                                                      │          └── [006 Cache]
Phase 3:                                              ├── [007 API (+09–12)] ─
                                                      │    └── [008 DB (+07–09)]
                                                      └── [009 Eval] ────────
Phase 4:                                                    │
                                                      [010 Frontend Foundation]
                                                            │
                                                      [011 Chat UI Core]
                                                            │
                                                      [012 Advanced Features]
```

## Updated Phase Exit Criteria

| Phase       | Exit Criteria                                                                                                            |
| ----------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Phase 0** | `make install && make test && make lint` passes. All modules importable.                                                 |
| **Phase 1** | Data pipeline produces valid `.jsonl`. FAISS index built and searchable. Baseline precision@5 measured.                  |
| **Phase 2** | End-to-end Q→A pipeline works. Query expansion improves recall. Caching operational. Metrics collected. Fallback tested. |
| **Phase 3** | All API endpoints functional. Database persists queries. Evaluation suite generates reports with all metrics. SSE streaming and analytics endpoints operational. |
| **Phase 4** | Frontend app builds and passes all tests. Chat UI sends/receives messages with streaming. Sources display with citations. Token/latency metrics visible. Conversations persist and switch. Model selection and retrieval tuning work. Export produces valid files. Analytics dashboard renders. E2E Playwright tests pass. |

---

## Review & Acceptance Checklist (Phase 4 additions)

- [ ] Frontend spec contains ONLY what/why — no library names
- [ ] Frontend plan contains ALL technical decisions — React, Tailwind, Zustand, etc.
- [ ] Every task has a clear file path and definition of done
- [ ] Every frontend task traces to a user story
- [ ] Backend API extensions (T007-09 through T008-09) are defined to support frontend needs
- [ ] Mock server (MSW) ensures frontend can be developed independently of backend
- [ ] E2E tests cover complete user journeys
- [ ] Dependency graph is acyclic — frontend depends on backend API, not internal modules
- [ ] No direct database or FAISS access from frontend — everything via API
- [ ] Accessibility basics covered (keyboard nav, ARIA labels, color contrast in both themes)

---

*Phase 4 follows the same Spec-Driven Development (SDD) methodology. Each feature is implemented via `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement` in sequence. The frontend is developed as a separate package within the monorepo, communicating with the backend exclusively through the REST API defined in Features 007/008.*
