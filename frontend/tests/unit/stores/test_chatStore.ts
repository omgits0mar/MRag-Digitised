import { beforeEach, describe, expect, it } from "vitest";

import { resetChatStore, useChatStore } from "@/stores/chatStore";

describe("chatStore", () => {
  beforeEach(() => {
    resetChatStore();
  });

  it("starts with the documented transcript defaults", () => {
    expect(useChatStore.getState()).toMatchObject({
      activeConversationId: null,
      focusedAssistantMessageId: null,
      inFlightRequest: null,
      isStreaming: false,
      lastError: null,
      messages: [],
    });
  });

  it("tracks message focus and lifecycle-aware in-flight request state", () => {
    useChatStore.getState().appendMessages([
      {
        content: "Question",
        conversationId: null,
        createdAt: "2026-04-15T08:00:00Z",
        id: "user-1",
        role: "user",
        status: "complete",
      },
      {
        content: "",
        conversationId: null,
        createdAt: "2026-04-15T08:00:00Z",
        id: "assistant-1",
        role: "assistant",
        status: "thinking",
      },
    ]);
    useChatStore.getState().beginRequest({
      assistantMessageId: "assistant-1",
      conversationId: null,
      mode: "stream",
      requestId: "req-1",
      submittedAt: "2026-04-15T08:00:00Z",
      userMessageId: "user-1",
    });
    useChatStore.getState().updateInFlightRequest({
      firstChunkAt: "2026-04-15T08:00:01Z",
    });

    expect(useChatStore.getState()).toMatchObject({
      focusedAssistantMessageId: "assistant-1",
      inFlightRequest: {
        assistantMessageId: "assistant-1",
        firstChunkAt: "2026-04-15T08:00:01Z",
      },
      isStreaming: true,
    });

    useChatStore.getState().finishRequest();
    expect(useChatStore.getState()).toMatchObject({
      inFlightRequest: null,
      isStreaming: false,
    });
  });

  it("hydrates a saved conversation and resets to a new chat cleanly", () => {
    useChatStore.getState().hydrateConversation({
      createdAt: "2026-04-10T08:30:00Z",
      id: "conv-1",
      messageCount: 2,
      messages: [
        {
          content: "Saved answer",
          conversationId: "conv-1",
          createdAt: "2026-04-10T08:31:00Z",
          id: "assistant-1",
          role: "assistant",
          status: "complete",
        },
      ],
      status: "loaded",
      title: "Saved conversation",
      updatedAt: "2026-04-10T08:31:00Z",
    });

    expect(useChatStore.getState()).toMatchObject({
      activeConversationId: "conv-1",
      focusedAssistantMessageId: "assistant-1",
      messages: [
        {
          id: "assistant-1",
        },
      ],
    });

    useChatStore.getState().startNewConversation();

    expect(useChatStore.getState()).toMatchObject({
      activeConversationId: null,
      focusedAssistantMessageId: null,
      messages: [],
    });
  });
});
