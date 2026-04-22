import { create } from "zustand";

import type {
  ApiError,
  ChatMessage,
  ConversationRecord,
  InFlightRequest,
} from "@/api/types";

export interface ChatStoreState {
  messages: ChatMessage[];
  activeConversationId: string | null;
  focusedAssistantMessageId: string | null;
  inFlightRequest: InFlightRequest | null;
  isStreaming: boolean;
  lastError: ApiError | null;
  appendMessage: (message: ChatMessage) => void;
  appendMessages: (messages: ChatMessage[]) => void;
  updateMessage: (messageId: string, updater: (message: ChatMessage) => ChatMessage) => void;
  setMessages: (messages: ChatMessage[], conversationId: string | null) => void;
  hydrateConversation: (conversation: ConversationRecord) => void;
  setFocusedAssistantMessage: (messageId: string | null) => void;
  beginRequest: (request: InFlightRequest) => void;
  updateInFlightRequest: (patch: Partial<InFlightRequest>) => void;
  finishRequest: () => void;
  setActiveConversation: (id: string | null) => void;
  setError: (error: ApiError | null) => void;
  startNewConversation: () => void;
  clear: () => void;
}

const CHAT_STORE_INITIAL_STATE = {
  messages: [],
  activeConversationId: null,
  focusedAssistantMessageId: null,
  inFlightRequest: null,
  isStreaming: false,
  lastError: null,
} satisfies Pick<
  ChatStoreState,
  | "messages"
  | "activeConversationId"
  | "focusedAssistantMessageId"
  | "inFlightRequest"
  | "isStreaming"
  | "lastError"
>;

function getFocusedAssistantId(messages: ChatMessage[]): string | null {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    if (message?.role === "assistant") {
      return message.id;
    }
  }

  return null;
}

export const useChatStore = create<ChatStoreState>()((set) => ({
  ...CHAT_STORE_INITIAL_STATE,
  appendMessage(message) {
    set((state) => ({
      activeConversationId: message.conversationId ?? state.activeConversationId,
      focusedAssistantMessageId:
        message.role === "assistant" ? message.id : state.focusedAssistantMessageId,
      lastError: null,
      messages: [...state.messages, message],
    }));
  },
  appendMessages(messages) {
    set((state) => {
      const nextMessages = [...state.messages, ...messages];
      const lastConversationId =
        [...messages].reverse().find((message) => message.conversationId !== null)?.conversationId ??
        state.activeConversationId;

      return {
        activeConversationId: lastConversationId,
        focusedAssistantMessageId: getFocusedAssistantId(nextMessages),
        lastError: null,
        messages: nextMessages,
      };
    });
  },
  updateMessage(messageId, updater) {
    set((state) => {
      const nextMessages = state.messages.map((message) =>
        message.id === messageId ? updater(message) : message,
      );

      return {
        activeConversationId:
          nextMessages.find((message) => message.id === messageId)?.conversationId ??
          state.activeConversationId,
        focusedAssistantMessageId: getFocusedAssistantId(nextMessages),
        messages: nextMessages,
      };
    });
  },
  setMessages(messages, conversationId) {
    set({
      activeConversationId: conversationId,
      focusedAssistantMessageId: getFocusedAssistantId(messages),
      inFlightRequest: null,
      isStreaming: false,
      lastError: null,
      messages,
    });
  },
  hydrateConversation(conversation) {
    set({
      activeConversationId: conversation.id,
      focusedAssistantMessageId: getFocusedAssistantId(conversation.messages ?? []),
      inFlightRequest: null,
      isStreaming: false,
      lastError: null,
      messages: conversation.messages ?? [],
    });
  },
  setFocusedAssistantMessage(messageId) {
    set({
      focusedAssistantMessageId: messageId,
    });
  },
  beginRequest(request) {
    set({
      inFlightRequest: request,
      isStreaming: true,
      lastError: null,
    });
  },
  updateInFlightRequest(patch) {
    set((state) => ({
      inFlightRequest:
        state.inFlightRequest === null ? null : { ...state.inFlightRequest, ...patch },
    }));
  },
  finishRequest() {
    set({
      inFlightRequest: null,
      isStreaming: false,
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
  startNewConversation() {
    set({
      ...CHAT_STORE_INITIAL_STATE,
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
