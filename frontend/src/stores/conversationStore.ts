import { create } from "zustand";

import {
  deleteConversation as deleteConversationRequest,
  getConversation,
  listConversations,
} from "@/api/endpoints";
import type { ApiError, ConversationRecord } from "@/api/types";
import { normalizeConversationRecord } from "@/api/types";
import { logger } from "@/lib/logger";

export interface ConversationStoreState {
  conversations: ConversationRecord[];
  activeId: string | null;
  isLoading: boolean;
  lastError: ApiError | null;
  loadConversations: () => Promise<void>;
  loadConversation: (id: string) => Promise<ConversationRecord | null>;
  selectConversation: (id: string | null) => void;
  clearActiveConversation: () => void;
  upsertConversation: (conversation: ConversationRecord) => void;
  replaceConversationMessages: (conversationId: string, messages: ConversationRecord["messages"]) => void;
  deleteConversation: (id: string) => Promise<boolean>;
  setError: (error: ApiError | null) => void;
}

const CONVERSATION_STORE_INITIAL_STATE = {
  conversations: [],
  activeId: null,
  isLoading: false,
  lastError: null,
} satisfies Pick<ConversationStoreState, "conversations" | "activeId" | "isLoading" | "lastError">;

let inFlightLoad: Promise<void> | null = null;
const inFlightDetailLoads = new Map<string, Promise<ConversationRecord | null>>();

function mergeConversation(
  conversations: ConversationRecord[],
  conversation: ConversationRecord,
): ConversationRecord[] {
  const existingIndex = conversations.findIndex((entry) => entry.id === conversation.id);

  if (existingIndex === -1) {
    return [conversation, ...conversations];
  }

  const next = [...conversations];
  next[existingIndex] = {
    ...next[existingIndex],
    ...conversation,
  };

  if (existingIndex === 0) {
    return next;
  }

  const [updated] = next.splice(existingIndex, 1);
  if (updated === undefined) {
    return next;
  }

  return [updated, ...next];
}

export const useConversationStore = create<ConversationStoreState>()((set, get) => ({
  ...CONVERSATION_STORE_INITIAL_STATE,
  async loadConversations() {
    if (inFlightLoad !== null) {
      return inFlightLoad;
    }

    const run = (async () => {
      set({
        isLoading: true,
      });

      const result = await listConversations();

      if (result.kind === "error") {
        set({
          isLoading: false,
          lastError: result.error,
        });
        return;
      }

      const conversations = result.data.map(normalizeConversationRecord);
      const previousActiveId = get().activeId;
      const hasActiveConversation =
        previousActiveId === null ||
        conversations.some((conversation) => conversation.id === previousActiveId);

      if (previousActiveId !== null && !hasActiveConversation) {
        logger.warn("conversations.active.missing", {
          activeId: previousActiveId,
        });
      }

      set({
        conversations,
        activeId: hasActiveConversation ? previousActiveId : null,
        isLoading: false,
        lastError: null,
      });
    })().finally(() => {
      inFlightLoad = null;
    });

    inFlightLoad = run;
    return run;
  },
  async loadConversation(id) {
    const cachedConversation = get().conversations.find(
      (conversation) => conversation.id === id && conversation.messages !== undefined,
    );
    if (cachedConversation !== undefined) {
      set({
        activeId: id,
        lastError: null,
      });
      return cachedConversation;
    }

    const existingLoad = inFlightDetailLoads.get(id);
    if (existingLoad !== undefined) {
      return existingLoad;
    }

    set((state) => ({
      activeId: id,
      conversations: state.conversations.map((conversation) =>
        conversation.id === id ? { ...conversation, status: "loading" } : conversation,
      ),
      lastError: null,
    }));

    const run = (async () => {
      const result = await getConversation(id);

      if (result.kind === "error") {
        set((state) => ({
          conversations: state.conversations.map((conversation) =>
            conversation.id === id ? { ...conversation, status: "idle" } : conversation,
          ),
          lastError: result.error,
        }));
        return null;
      }

      const conversation = normalizeConversationRecord(result.data);
      set((state) => ({
        activeId: id,
        conversations: mergeConversation(state.conversations, conversation),
        lastError: null,
      }));
      return conversation;
    })().finally(() => {
      inFlightDetailLoads.delete(id);
    });

    inFlightDetailLoads.set(id, run);
    return run;
  },
  selectConversation(id) {
    set({
      activeId: id,
    });
  },
  clearActiveConversation() {
    set({
      activeId: null,
    });
  },
  upsertConversation(conversation) {
    set((state) => ({
      conversations: mergeConversation(state.conversations, conversation),
    }));
  },
  replaceConversationMessages(conversationId, messages) {
    set((state) => ({
      conversations: state.conversations.map((conversation) =>
        conversation.id === conversationId
          ? {
              ...conversation,
              messages,
              messageCount: messages?.length ?? conversation.messageCount,
              status: messages === undefined ? conversation.status : "loaded",
              updatedAt: new Date().toISOString(),
            }
          : conversation,
      ),
    }));
  },
  async deleteConversation(id) {
    const snapshot = get().conversations;
    const previousActiveId = get().activeId;

    set({
      activeId: previousActiveId === id ? null : previousActiveId,
      conversations: snapshot.filter((conversation) => conversation.id !== id),
    });

    const result = await deleteConversationRequest(id);

    if (result.kind === "error") {
      set({
        activeId: previousActiveId,
        conversations: snapshot,
        lastError: result.error,
      });
      return false;
    }

    set({
      lastError: null,
    });
    return true;
  },
  setError(error) {
    set({
      lastError: error,
    });
  },
}));

export function resetConversationStore(): void {
  inFlightLoad = null;
  inFlightDetailLoads.clear();
  useConversationStore.setState(CONVERSATION_STORE_INITIAL_STATE);
}
