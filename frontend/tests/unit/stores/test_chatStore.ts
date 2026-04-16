import { beforeEach, describe, expect, it, vi } from "vitest";

import { logger } from "@/lib/logger";
import { resetChatStore, useChatStore } from "@/stores/chatStore";

describe("chatStore", () => {
  beforeEach(() => {
    resetChatStore();
    vi.restoreAllMocks();
  });

  it("starts with the documented session defaults", () => {
    expect(useChatStore.getState()).toMatchObject({
      activeConversationId: null,
      isStreaming: false,
      lastError: null,
      messages: [],
    });
  });

  it("tracks messages, conversation selection, and preserves the active conversation when cleared", () => {
    useChatStore.getState().setActiveConversation("conv-1");
    useChatStore.getState().addMessage({
      content: "Hello",
      conversation_id: "conv-1",
      created_at: "2026-04-12T10:00:00Z",
      id: "msg-1",
      role: "assistant",
    });
    useChatStore.getState().appendToLastAssistant(" world");
    useChatStore.getState().setStreaming(true);

    expect(useChatStore.getState()).toMatchObject({
      activeConversationId: "conv-1",
      isStreaming: true,
      messages: [
        {
          content: "Hello world",
          id: "msg-1",
          role: "assistant",
        },
      ],
    });

    useChatStore.getState().clear();

    expect(useChatStore.getState()).toMatchObject({
      activeConversationId: "conv-1",
      isStreaming: false,
      lastError: null,
      messages: [],
    });
  });

  it("no-ops and logs a warning when streaming chunks target a non-assistant message", () => {
    const warnSpy = vi.spyOn(logger, "warn").mockImplementation(() => undefined);

    useChatStore.getState().addMessage({
      content: "Question",
      conversation_id: "conv-2",
      created_at: "2026-04-12T10:05:00Z",
      id: "msg-2",
      role: "user",
    });
    useChatStore.getState().appendToLastAssistant(" ignored");

    expect(useChatStore.getState().messages[0]?.content).toBe("Question");
    expect(warnSpy).toHaveBeenCalledWith(
      "chat.append.invalid",
      expect.objectContaining({
        messageCount: 1,
      }),
    );
  });
});

