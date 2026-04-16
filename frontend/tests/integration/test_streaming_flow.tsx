import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/api/streaming", () => ({
  isStreamingUnsupported: vi.fn(() => false),
  streamAnswer: vi.fn(),
}));

import { streamAnswer } from "@/api/streaming";
import { setConfigForTests } from "@/config";
import { routes } from "@/router";
import { resetChatStore } from "@/stores/chatStore";
import { resetConversationStore } from "@/stores/conversationStore";

const mockedStreamAnswer = vi.mocked(streamAnswer);

function renderChatPage() {
  const router = createMemoryRouter(routes, {
    initialEntries: ["/"],
  });

  return render(<RouterProvider router={router} />);
}

describe("streaming chat flow", () => {
  beforeEach(() => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1440,
      writable: true,
    });

    setConfigForTests({
      apiBaseUrl: "http://localhost:8000",
      apiRequestTimeoutMs: 500,
      defaultModel: "llama-3.1-8b-instant",
      enableMock: true,
      enableStreaming: true,
    });

    resetChatStore();
    resetConversationStore();
    mockedStreamAnswer.mockReset();
  });

  it("streams an answer and expands assistant metadata", async () => {
    mockedStreamAnswer.mockImplementationOnce(async (_request, options) => {
      options?.onEvent?.({
        type: "start",
        conversation_id: "conv-1",
      });
      options?.onEvent?.({
        type: "token",
        content: "## Response for What is streamed?\n\n",
      });
      options?.onEvent?.({
        type: "token",
        content: "Streaming answers still show metadata.",
      });

      return {
        kind: "ok",
        data: {
          answer: "## Response for What is streamed?\n\nStreaming answers still show metadata.",
          conversation_id: "conv-1",
          is_fallback: false,
          latency: {
            generation_ms: 120,
            retrieval_ms: 60,
            search_ms: 25,
            total_ms: 205,
          },
          token_usage: {
            completion_tokens: 44,
            prompt_tokens: 71,
            total_tokens: 115,
          },
        },
      };
    });

    const user = userEvent.setup();
    renderChatPage();

    await user.type(await screen.findByLabelText(/ask a question/i), "What is streamed?");
    await user.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => {
      expect(mockedStreamAnswer).toHaveBeenCalledTimes(1);
    });
    expect(
      await screen.findByText(/^Streaming answers still show metadata\.$/i),
    ).toBeInTheDocument();

    await user.click(await screen.findByRole("button", { name: /details/i }));
    expect(await screen.findByText(/prompt tokens/i)).toBeInTheDocument();
    expect(screen.getByText(/total latency/i)).toBeInTheDocument();
  });

  it("retries a failed stream inline and replaces it with a successful answer", async () => {
    mockedStreamAnswer
      .mockResolvedValueOnce({
        kind: "error",
        error: {
          kind: "backend_error",
          status: 500,
          message: "Mock stream failure",
          detail: "Temporary upstream failure.",
        },
      })
      .mockImplementationOnce(async (_request, options) => {
        options?.onEvent?.({
          type: "start",
          conversation_id: "conv-retry",
        });
        options?.onEvent?.({
          type: "token",
          content: "Recovered answer",
        });

        return {
          kind: "ok",
          data: {
            answer: "Recovered answer",
            conversation_id: "conv-retry",
            is_fallback: false,
          },
        };
      });

    const user = userEvent.setup();
    renderChatPage();

    await user.type(await screen.findByLabelText(/ask a question/i), "Recover the stream");
    await user.click(screen.getByRole("button", { name: /send/i }));

    await user.click(await screen.findByRole("button", { name: /retry/i }));

    expect(await screen.findByText(/recovered answer/i)).toBeInTheDocument();
  });
});
