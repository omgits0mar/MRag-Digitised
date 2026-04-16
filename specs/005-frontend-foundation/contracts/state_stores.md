# Contract: Frontend State Stores

**Module**: `frontend/src/stores/`
**Files**: `chatStore.ts`, `conversationStore.ts`, `settingsStore.ts`

This contract defines the public shape (state + actions) of each Zustand store, the persistence policy, and the inter-store invariants. The store data types themselves are defined in `data-model.md` and re-summarised here only where needed for the contract.

---

## 1. Cross-cutting rules

- **No cross-store imports**: a store module MUST NOT `import` from another store module. Components compose stores via selectors; business logic that spans stores lives in hooks (`src/hooks/`).
- **No store → component imports**: stores MUST NOT import React components.
- **Selectors are the read API**: components subscribe via selectors (`useChatStore(s => s.messages)`), never by reading the whole state snapshot.
- **Actions are pure state transitions OR thin async wrappers around endpoints**: no business logic inside the store (e.g. title auto-generation, retrieval parameter validation). Complex orchestration lives in hooks.
- **Error channel**: every store exposes `lastError: ApiError | null` and `setError(e)` so components can render a consistent error surface.
- **Zustand middleware**: only `settingsStore` uses `persist`. `chatStore` and `conversationStore` are plain stores.

---

## 2. `chatStore`

### State

```ts
{
  messages: ChatMessage[];
  activeConversationId: string | null;
  isStreaming: boolean;
  lastError: ApiError | null;
}
```

### Actions

```ts
addMessage(message: ChatMessage): void;
appendToLastAssistant(chunk: string): void;
setStreaming(value: boolean): void;
setActiveConversation(id: string | null): void;
setError(error: ApiError | null): void;
clear(): void;
```

### Invariants

- `isStreaming === true` requires `messages[messages.length - 1]?.role === "assistant"`.
- `appendToLastAssistant(chunk)` is a no-op if the last message is not an assistant message (logged as a warning); this keeps Feature 006 streaming integration from corrupting the store.
- `clear()` resets `messages`, `isStreaming`, `lastError` but preserves `activeConversationId`.
- `setActiveConversation(id)` MUST be followed by either an in-memory rehydrate or a backend fetch; Feature 006 is responsible for orchestration, but `chatStore` itself does not call the API.

### Persistence

None. Session-scoped.

### Initial state

```ts
{ messages: [], activeConversationId: null, isStreaming: false, lastError: null }
```

---

## 3. `conversationStore`

### State

```ts
{
  conversations: ConversationSummary[];
  activeId: string | null;
  isLoading: boolean;
  lastError: ApiError | null;
}
```

### Actions

```ts
loadConversations(): Promise<void>;
selectConversation(id: string | null): void;
deleteConversation(id: string): Promise<void>;
setError(error: ApiError | null): void;
```

### Behaviour

- `loadConversations()` calls `endpoints.listConversations()`:
  - `ok`: replace `conversations` with response, clear `lastError`.
  - `error`: preserve the existing list, set `lastError` to the `ApiError`.
  - The action always flips `isLoading` true→false around the call.
- `deleteConversation(id)` is optimistic:
  1. Snapshot the current list.
  2. Remove the entry locally.
  3. If `activeId === id`, set `activeId = null`.
  4. Call `endpoints.deleteConversation(id)`.
  5. On error, restore the snapshot and surface the `ApiError` via `lastError`.
- `selectConversation(id)` updates `activeId` only; it does NOT trigger a fetch (Feature 006 composes the fetch via a hook).

### Invariants

- If `activeId !== null`, then after `loadConversations()` resolves, either `conversations.find(c => c.id === activeId)` exists OR `activeId` is reset to `null` and a non-blocking warning is logged.
- `isLoading` is true while any `loadConversations()` promise is in flight; concurrent calls are serialised (later calls await the in-flight one).

### Persistence

None.

### Initial state

```ts
{ conversations: [], activeId: null, isLoading: false, lastError: null }
```

---

## 4. `settingsStore`

### State

```ts
{
  schemaVersion: 1;
  selectedModel: string;
  topK: number;           // 1..20
  scoreThreshold: number; // 0..1
  temperature: number;    // 0..2
  theme: "system" | "light" | "dark";
}
```

### Actions

```ts
setModel(model: string): void;
setTopK(value: number): void;
setScoreThreshold(value: number): void;
setTemperature(value: number): void;
setTheme(theme: Theme): void;
resetDefaults(): void;
```

### Behaviour

- Each setter **clamps and validates** per the rules in `data-model.md` §3.3. Invalid values are rejected silently (no state change) and `logger.warn("settings.invalid", { key, value, reason })` is emitted.
- `resetDefaults()` replaces the state with `SETTINGS_DEFAULTS` (from `config.ts`) while preserving `schemaVersion`.
- The store is **the authoritative source** of user preferences. Components MUST NOT cache preference values in their own state.

### Persistence

- Middleware: `zustand/middleware`'s `persist` with:
  - `name: "mrag:settings:v1"`
  - `storage: createJSONStorage(() => localStorage)`
  - `version: 1`
  - `partialize: (s) => ({ schemaVersion, selectedModel, topK, scoreThreshold, temperature, theme })` — exports only the preference fields, never derived/runtime values.
  - `migrate: (persistedState, version) => SETTINGS_DEFAULTS if version !== 1`
  - `onRehydrateStorage: () => (state, error) => if (error) logger.warn("settings.rehydrate.failed", ...)`

### Invariants

- `schemaVersion` is always `1` in v1 of this feature. Bumping requires writing a migration function (see `data-model.md` §6).
- `selectedModel` is never empty; `setModel("")` is rejected.
- `theme` mutations immediately trigger the `<html>` class toggle via `ThemeProvider`'s `useEffect` — components never read `document.documentElement` directly.

### Initial state

Hydrated from `localStorage` if a compatible blob exists; otherwise `SETTINGS_DEFAULTS` from `config.ts`.

---

## 5. Test requirements

Each store MUST have a unit test file under `frontend/tests/unit/stores/` covering:

1. **Initial state** matches the specification above.
2. **Each action** produces the documented state transition.
3. **Invariants** hold after action sequences (especially `appendToLastAssistant` no-op guard and `deleteConversation` optimistic-rollback).
4. **Persistence (settingsStore only)**:
    - Writing a value and creating a new store instance reads it back.
    - A corrupt `localStorage` blob (non-JSON) falls back to defaults without throwing.
    - A `schemaVersion: 999` blob falls back to defaults.

---

## 6. Extension points for downstream features

- **Feature 006 Chat UI Core** will add a `sendMessage()` action to `chatStore` that orchestrates `endpoints.askQuestion()` and streams into `appendToLastAssistant`. The hook-level orchestration (not the store) is where `settingsStore` values (topK, threshold, temperature, selectedModel) are read and forwarded.
- **Feature 007 Advanced Chat Features** will add an `availableModels: ModelInfo[]` slice to `settingsStore` (populated by `endpoints.listModels()` once per session). That addition bumps `schemaVersion` to `2` and ships a migration.
