import { create } from "zustand";

import type { ApiError, SourceResponse } from "@/api/types";
import { logger } from "@/lib/logger";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  conversation_id: string | null;
  sources?: SourceResponse[];
  confidence_score?: number;
  response_time_ms?: number;
  is_fallback?: boolean;
  isStreaming?: boolean;
  error?: string;
}

export interface ChatStoreState {
  messages: ChatMessage[];
  activeConversationId: string | null;
  isStreaming: boolean;
  lastError: ApiError | null;
  addMessage: (message: ChatMessage) => void;
  appendToLastAssistant: (chunk: string) => void;
  setStreaming: (value: boolean) => void;
  setActiveConversation: (id: string | null) => void;
  setError: (error: ApiError | null) => void;
  clear: () => void;
}

const CHAT_STORE_INITIAL_STATE = {
  messages: [],
  activeConversationId: null,
  isStreaming: false,
  lastError: null,
} satisfies Pick<
  ChatStoreState,
  "messages" | "activeConversationId" | "isStreaming" | "lastError"
>;

export const useChatStore = create<ChatStoreState>()((set, get) => ({
  ...CHAT_STORE_INITIAL_STATE,
  addMessage(message) {
    set((state) => ({
      activeConversationId: message.conversation_id ?? state.activeConversationId,
      lastError: null,
      messages: [...state.messages, message],
    }));
  },
  appendToLastAssistant(chunk) {
    const messages = get().messages;
    const lastMessage = messages[messages.length - 1];

    if (lastMessage?.role !== "assistant") {
      logger.warn("chat.append.invalid", {
        chunkLength: chunk.length,
        messageCount: messages.length,
      });
      return;
    }

    const nextMessages = [...messages];
    nextMessages[nextMessages.length - 1] = {
      ...lastMessage,
      content: `${lastMessage.content}${chunk}`,
    };

    set({
      messages: nextMessages,
    });
  },
  setStreaming(value) {
    set({
      isStreaming: value,
    });
  },
  setActiveConversation(id) {
    set({
      activeConversationId: id,
    });
  },
  setError(error) {
    set({
      lastError: error,
    });
  },
  clear() {
    set((state) => ({
      ...CHAT_STORE_INITIAL_STATE,
      activeConversationId: state.activeConversationId,
    }));
  },
}));

export function resetChatStore(): void {
  useChatStore.setState(CHAT_STORE_INITIAL_STATE);
}

