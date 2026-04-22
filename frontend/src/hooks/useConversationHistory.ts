import { useEffect } from "react";

import { useChatStore } from "@/stores/chatStore";
import { useConversationStore } from "@/stores/conversationStore";

interface UseConversationHistoryOptions {
  beforeTranscriptChange?: () => Promise<void> | void;
}

export function useConversationHistory(
  options: UseConversationHistoryOptions = {},
) {
  const conversations = useConversationStore((state) => state.conversations);
  const activeId = useConversationStore((state) => state.activeId);
  const isLoading = useConversationStore((state) => state.isLoading);
  const lastError = useConversationStore((state) => state.lastError);
  const loadConversations = useConversationStore((state) => state.loadConversations);
  const loadConversation = useConversationStore((state) => state.loadConversation);
  const clearActiveConversation = useConversationStore((state) => state.clearActiveConversation);
  const deleteConversationRequest = useConversationStore((state) => state.deleteConversation);

  const hydrateConversation = useChatStore((state) => state.hydrateConversation);
  const startNewConversationState = useChatStore((state) => state.startNewConversation);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  async function selectConversation(id: string): Promise<void> {
    await options.beforeTranscriptChange?.();
    const conversation = await loadConversation(id);

    if (conversation !== null) {
      hydrateConversation(conversation);
    }
  }

  async function startNewConversation(): Promise<void> {
    await options.beforeTranscriptChange?.();
    clearActiveConversation();
    startNewConversationState();
  }

  async function deleteConversation(id: string): Promise<void> {
    await options.beforeTranscriptChange?.();
    const removed = await deleteConversationRequest(id);

    if (removed && activeId === id) {
      startNewConversationState();
    }
  }

  return {
    activeId,
    conversations,
    deleteConversation,
    isLoading,
    lastError,
    selectConversation,
    startNewConversation,
  };
}
