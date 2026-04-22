# Contract: Chat State and UI Orchestration

**Modules**: `frontend/src/stores/`, `frontend/src/hooks/`, `frontend/src/components/chat/`, `frontend/src/components/conversations/`

This contract defines how Feature 006 coordinates stores, hooks, and presentational components.

---

## 1. Cross-cutting rules

- Stores own serializable state; hooks own transport handles and orchestration.
- Components are presentational: they receive typed props and callbacks, but do not call the API seam directly.
- `settingsStore` remains read-only input for this feature; chat submission reads its values when constructing requests but does not change settings behaviour.
- Retry, cancel, and conversation switching always operate through hook actions so they can coordinate store updates, abort signals, and scroll/focus state in one place.

---

## 2. `chatStore`

### State

```ts
{
  messages: ChatMessage[];
  activeConversationId: string | null;
  focusedAssistantMessageId: string | null;
  inFlight: InFlightRequest | null;
  jumpToLatestVisible: boolean;
  sourcePanelOpen: boolean;
  lastError: ApiError | null;
}
```

### Required actions

```ts
replaceMessages(messages: ChatMessage[], conversationId: string | null): void;
appendUserMessage(message: ChatMessage): void;
beginAssistantMessage(message: ChatMessage, request: InFlightRequest): void;
appendAssistantChunk(messageId: string, chunk: string): void;
completeAssistantMessage(messageId: string, patch: AssistantCompletionPatch): void;
markAssistantCancelled(messageId: string): void;
markAssistantInterrupted(messageId: string): void;
markAssistantError(messageId: string, error: ApiError): void;
focusAssistantMessage(messageId: string | null): void;
setJumpToLatestVisible(value: boolean): void;
setSourcePanelOpen(value: boolean): void;
clearForNewChat(): void;
setLastError(error: ApiError | null): void;
```

### Invariants

- `inFlight !== null` implies the assistant message with `assistantMessageId` exists in `messages`.
- `focusedAssistantMessageId` must always point at an assistant message or be `null`.
- `clearForNewChat()` resets transcript and in-flight state but does not delete prior conversation summaries from `conversationStore`.

---

## 3. `conversationStore`

### State

```ts
{
  conversations: ConversationSummary[];
  activeId: string | null;
  isLoadingList: boolean;
  isLoadingDetail: boolean;
  deletingId: string | null;
  lastError: ApiError | null;
}
```

### Required actions

```ts
loadConversations(): Promise<void>;
loadConversationDetail(id: string): Promise<ConversationDetail | null>;
selectConversation(id: string | null): void;
deleteConversation(id: string): Promise<boolean>;
upsertConversationSummary(summary: ConversationSummary): void;
setLastError(error: ApiError | null): void;
```

### Invariants

- Deletion is optimistic only if rollback is supported with the pre-delete snapshot.
- Selecting a conversation must never leak the prior conversation’s in-flight assistant message into the new transcript.
- Loading detail does not mutate `chatStore` directly; the controller hook performs the transcript replacement after cancellation checks.

---

## 4. Orchestration hooks

### 4.1 `useChatSession()`

Primary controller for:

- `sendMessage(question: string): Promise<void>`
- `cancelMessage(): void`
- `retryMessage(userMessageId: string): Promise<void>`
- `startNewChat(): void`
- `selectConversation(id: string): Promise<void>`
- `deleteConversation(id: string): Promise<void>`

**Responsibilities**

- Read settings from `settingsStore`.
- Create user and assistant placeholder messages.
- Start streaming or one-shot requests via the API seam.
- Own the live `AbortController`.
- Map transport outcomes into chat/conversation store transitions.
- Ensure cancellation happens before conversation switching/deletion.

### 4.2 `useConversationHistory()`

Shared list/detail loader for the Chat and History routes.

**Responsibilities**

- Bootstraps conversation summaries on mount.
- Exposes list state and delete/select callbacks to conversation list components.
- Keeps the currently active conversation summary synchronized when a response completes and returns/creates a conversation id.

### 4.3 `useTranscriptScroll()`

**Responsibilities**

- Track whether the user is pinned to the bottom of the transcript.
- Auto-scroll on new content only when pinned.
- Raise/lower `jumpToLatestVisible`.
- Support explicit “scroll newest into view” when retry/citation focus changes the active message.

---

## 5. Presentational components

### Chat components

- `ChatWorkspace`
  - Composes the transcript, source panel, composer, and conversation rail entry points.
- `ChatComposer`
  - Owns only local textarea value and keyboard handling (`Enter` submit, `Shift+Enter` newline).
- `MessageList`
  - Renders ordered `ChatMessage[]` and forwards focus/scroll refs.
- `MessageBubble`
  - Renders one message body plus role styling, markdown, and inline error/cancel/interrupted affordances.
- `MessageMeta`
  - Renders token/latency/cache signals and expandable detail rows only when data exists.
- `InlineAssistantState`
  - Shared treatment for thinking/error/interrupted/cancelled/low-confidence markers.
- `SourcePanel`
  - Reads the focused assistant message and renders the current source set or the explicit empty/no-sources state.
- `SourceCard`
  - Handles truncation/expansion, relevance visuals, and focus highlighting.
- `JumpToLatestButton`
  - Appears only when the transcript has new unseen content.

### Conversation components

- `ConversationList`
  - Renders a reusable list for both Chat and History routes.
- `ConversationListItem`
  - Shows title, timestamp, message count, active state, and delete affordance.
- `DeleteConversationConfirm`
  - Inline explicit confirm/cancel UI; no modal library required.

---

## 6. Accessibility contract

- Every interactive control introduced by the feature must expose an accessible name.
- Citation controls must be keyboard-activatable and move focus/context to the matching source card.
- Delete confirmation must include both confirm and cancel paths reachable by keyboard.
- Visible focus styles must be retained on send, cancel, retry, citations, source expansion, conversation selection/deletion, and metadata expansion.
- Message content containers should use `dir="auto"` so RTL and mixed-script text render naturally.

---

## 7. Testing contract

At minimum, Feature 006 must add coverage for:

1. `chatStore` transitions across complete/cancelled/interrupted/error paths.
2. `streaming.ts` parser handling `chunk`, `complete`, transport interruption, and `unavailable`.
3. Chat-page happy path in mock streaming mode.
4. History-page conversation switching and delete confirmation.
5. Accessibility checks for empty, streaming, error, populated-with-sources, and low-confidence states.
