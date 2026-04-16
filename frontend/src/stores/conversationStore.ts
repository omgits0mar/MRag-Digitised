import { create } from "zustand";

import {
  deleteConversation as deleteConversationRequest,
  listConversations,
} from "@/api/endpoints";
import type { ApiError, ConversationSummary } from "@/api/types";
import { logger } from "@/lib/logger";

export interface ConversationStoreState {
  conversations: ConversationSummary[];
  activeId: string | null;
  isLoading: boolean;
  lastError: ApiError | null;
  loadConversations: () => Promise<void>;
  selectConversation: (id: string | null) => void;
  deleteConversation: (id: string) => Promise<void>;
  setError: (error: ApiError | null) => void;
}

const CONVERSATION_STORE_INITIAL_STATE = {
  conversations: [],
  activeId: null,
  isLoading: false,
  lastError: null,
} satisfies Pick<
  ConversationStoreState,
  "conversations" | "activeId" | "isLoading" | "lastError"
>;

let inFlightLoad: Promise<void> | null = null;

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

      const previousActiveId = get().activeId;
      const hasActiveConversation =
        previousActiveId === null ||
        result.data.some((conversation) => conversation.id === previousActiveId);

      if (previousActiveId !== null && !hasActiveConversation) {
        logger.warn("conversations.active.missing", {
          activeId: previousActiveId,
        });
      }

      set({
        conversations: result.data,
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
  selectConversation(id) {
    set({
      activeId: id,
    });
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
      return;
    }

    set({
      lastError: null,
    });
  },
  setError(error) {
    set({
      lastError: error,
    });
  },
}));

export function resetConversationStore(): void {
  inFlightLoad = null;
  useConversationStore.setState(CONVERSATION_STORE_INITIAL_STATE);
}

