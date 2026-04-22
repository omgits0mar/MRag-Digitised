import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";

import { setConfigForTests } from "@/config";
import { routes } from "@/router";
import { resetChatStore } from "@/stores/chatStore";
import { resetConversationStore } from "@/stores/conversationStore";

function renderHistoryPage() {
  const router = createMemoryRouter(routes, {
    initialEntries: ["/history"],
  });

  return render(<RouterProvider router={router} />);
}

describe("History page", () => {
  beforeEach(() => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1440,
      writable: true,
    });

    setConfigForTests({
      apiBaseUrl: "http://localhost:8000",
      apiRequestTimeoutMs: 2_000,
      defaultModel: "llama-3.1-8b-instant",
      enableMock: true,
      enableStreaming: false,
    });

    resetChatStore();
    resetConversationStore();
  });

  it("loads, switches, and deletes conversations with confirmation", async () => {
    const user = userEvent.setup();
    renderHistoryPage();

    expect(await screen.findByRole("heading", { name: /review saved transcripts/i })).toBeInTheDocument();
    expect(await screen.findByText(/arabic policy translation review/i)).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: /kurdish dataset quality pass.*messages/i,
      }),
    );
    expect(
      await screen.findByText((content) => content.includes("Three low-confidence cases cluster")),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /delete arabic policy translation review/i }));
    expect(await screen.findByText(/delete “arabic policy translation review”/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /^delete$/i }));

    expect(screen.queryByText(/arabic policy translation review/i)).not.toBeInTheDocument();
  });
});
