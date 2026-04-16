import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/api/endpoints", () => ({
  deleteConversation: vi.fn(),
  getConversation: vi.fn(),
  listConversations: vi.fn(),
}));

import {
  deleteConversation,
  getConversation,
  listConversations,
} from "@/api/endpoints";
import { logger } from "@/lib/logger";
import {
  resetConversationStore,
  useConversationStore,
} from "@/stores/conversationStore";

const mockedDeleteConversation = vi.mocked(deleteConversation);
const mockedGetConversation = vi.mocked(getConversation);
const mockedListConversations = vi.mocked(listConversations);

describe("conversationStore", () => {
  beforeEach(() => {
    resetConversationStore();
    vi.clearAllMocks();
  });

  it("loads summaries and clears stale active selections", async () => {
    const warnSpy = vi.spyOn(logger, "warn").mockImplementation(() => undefined);

    mockedListConversations.mockResolvedValueOnce({
      kind: "ok",
      data: [
        {
          created_at: "2026-04-12T09:00:00Z",
          id: "conv-1",
          message_count: 2,
          title: "One",
          updated_at: "2026-04-12T09:30:00Z",
        },
      ],
    });

    useConversationStore.getState().selectConversation("missing");
    await useConversationStore.getState().loadConversations();

    expect(useConversationStore.getState()).toMatchObject({
      activeId: null,
      conversations: [
        {
          id: "conv-1",
          title: "One",
          updatedAt: "2026-04-12T09:30:00Z",
        },
      ],
      isLoading: false,
      lastError: null,
    });
    expect(warnSpy).toHaveBeenCalledWith(
      "conversations.active.missing",
      expect.objectContaining({
        activeId: "missing",
      }),
    );
  });

  it("hydrates conversation detail on demand", async () => {
    mockedGetConversation.mockResolvedValueOnce({
      kind: "ok",
      data: {
        created_at: "2026-04-12T09:00:00Z",
        id: "conv-1",
        message_count: 2,
        messages: [
          {
            content: "Hello",
            created_at: "2026-04-12T09:00:00Z",
            id: "msg-1",
            role: "user",
          },
          {
            content: "Hi",
            created_at: "2026-04-12T09:01:00Z",
            id: "msg-2",
            role: "assistant",
          },
        ],
        title: "One",
        updated_at: "2026-04-12T09:30:00Z",
      },
    });

    const conversation = await useConversationStore.getState().loadConversation("conv-1");

    expect(conversation?.id).toBe("conv-1");
    expect(conversation?.status).toBe("loaded");
    expect(conversation?.messages?.[0]).toMatchObject({
      conversationId: "conv-1",
      id: "msg-1",
    });
  });

  it("restores optimistic deletes on failure", async () => {
    const existingConversations = [
      {
        createdAt: "2026-04-12T09:00:00Z",
        id: "conv-1",
        messageCount: 2,
        title: "One",
        updatedAt: "2026-04-12T09:30:00Z",
      },
      {
        createdAt: "2026-04-12T10:00:00Z",
        id: "conv-2",
        messageCount: 3,
        title: "Two",
        updatedAt: "2026-04-12T10:30:00Z",
      },
    ];

    useConversationStore.setState({
      activeId: "conv-1",
      conversations: existingConversations,
      isLoading: false,
      lastError: null,
    });

    mockedDeleteConversation.mockResolvedValueOnce({
      kind: "error",
      error: {
        kind: "network",
        message: "Backend is unreachable.",
      },
    });

    await useConversationStore.getState().deleteConversation("conv-1");

    expect(useConversationStore.getState()).toMatchObject({
      activeId: "conv-1",
      conversations: existingConversations,
      lastError: {
        kind: "network",
        message: "Backend is unreachable.",
      },
    });
  });
});
