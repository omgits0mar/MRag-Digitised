import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/api/endpoints", () => ({
  deleteConversation: vi.fn(),
  listConversations: vi.fn(),
}));

import { deleteConversation, listConversations } from "@/api/endpoints";
import { logger } from "@/lib/logger";
import {
  resetConversationStore,
  useConversationStore,
} from "@/stores/conversationStore";

const mockedDeleteConversation = vi.mocked(deleteConversation);
const mockedListConversations = vi.mocked(listConversations);

describe("conversationStore", () => {
  beforeEach(() => {
    resetConversationStore();
    vi.clearAllMocks();
  });

  it("loads conversations and clears a stale active selection", async () => {
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

  it("restores optimistic deletes on failure", async () => {
    const existingConversations = [
      {
        created_at: "2026-04-12T09:00:00Z",
        id: "conv-1",
        message_count: 2,
        title: "One",
        updated_at: "2026-04-12T09:30:00Z",
      },
      {
        created_at: "2026-04-12T10:00:00Z",
        id: "conv-2",
        message_count: 3,
        title: "Two",
        updated_at: "2026-04-12T10:30:00Z",
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

