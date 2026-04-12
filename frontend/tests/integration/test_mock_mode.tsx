import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";

import { setConfigForTests } from "@/config";
import { routes } from "@/router";
import { resetChatStore } from "@/stores/chatStore";
import {
  resetConversationStore,
  useConversationStore,
} from "@/stores/conversationStore";
import { rehydrateSettingsStore, resetSettingsStore } from "@/stores/settingsStore";

function renderMockApp(initialEntries: string[] = ["/"]) {
  const router = createMemoryRouter(routes, {
    initialEntries,
  });

  return render(<RouterProvider router={router} />);
}

describe("mock mode", () => {
  beforeEach(async () => {
    localStorage.clear();
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1280,
      writable: true,
    });

    setConfigForTests({
      apiBaseUrl: "http://localhost:8000",
      apiRequestTimeoutMs: 30_000,
      defaultModel: "llama-3.1-8b-instant",
      enableMock: true,
      enableStreaming: false,
    });

    resetChatStore();
    resetConversationStore();
    resetSettingsStore();
    await rehydrateSettingsStore();
  });

  it("renders every top-level view with mock-backed data", async () => {
    const user = userEvent.setup();

    renderMockApp(["/history"]);

    expect(await screen.findByText(/backend healthy/i)).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", {
        name: /conversation history is wired to shared state/i,
      }),
    ).toBeInTheDocument();
    expect(await screen.findByText(/arabic policy translation review/i)).toBeInTheDocument();

    const openButtons = await screen.findAllByRole("button", { name: "Open" });
    await user.click(openButtons[0]!);

    expect(useConversationStore.getState().activeId).toBe("conv-1");

    cleanup();
    renderMockApp(["/settings"]);

    expect(
      await screen.findByRole("heading", {
        name: /preferences already persist across reloads/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/selected model/i)).toHaveValue("llama-3.1-8b-instant");

    cleanup();
    renderMockApp(["/"]);

    expect(
      await screen.findByRole("heading", {
        name: /ask multilingual questions with confidence/i,
      }),
    ).toBeInTheDocument();
  });
});
