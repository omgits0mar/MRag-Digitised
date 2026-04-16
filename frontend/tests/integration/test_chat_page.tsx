import axe from "axe-core";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";

import { setConfigForTests } from "@/config";
import { routes } from "@/router";
import { resetChatStore } from "@/stores/chatStore";
import { resetConversationStore } from "@/stores/conversationStore";

function renderChatPage() {
  const router = createMemoryRouter(routes, {
    initialEntries: ["/"],
  });

  return render(<RouterProvider router={router} />);
}

async function assertNoCriticalAxeViolations(container: HTMLElement): Promise<void> {
  const results = await axe.run(container, {
    runOnly: { type: "tag", values: ["wcag2a", "wcag2aa"] },
    resultTypes: ["violations"],
  });
  const critical = results.violations.filter((violation) => violation.impact === "critical");
  expect(critical).toEqual([]);
}

describe("Chat page", () => {
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

  it("submits a question, preserves Shift+Enter, and renders sources", async () => {
    const user = userEvent.setup();
    const { container } = renderChatPage();

    const composer = await screen.findByLabelText(/ask a question/i);
    await user.type(composer, "What are the main stages");
    await user.keyboard("{Shift>}{Enter}{/Shift}");
    await user.type(composer, "of the MRAG pipeline?");

    expect(composer).toHaveValue("What are the main stages\nof the MRAG pipeline?");

    await user.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => {
      expect(composer).toHaveValue("");
    });
    expect(
      await screen.findByRole("heading", {
        name: /response for what are the main stages/i,
      }),
    ).toBeInTheDocument();
    expect(await screen.findByText(/doc-pipeline-001/i)).toBeInTheDocument();
    expect(screen.getByText(/validated multilingual chunks move through ingestion/i)).toBeInTheDocument();

    await assertNoCriticalAxeViolations(container);
  });

  it("shows a low-confidence no-sources state for fallback responses", async () => {
    const user = userEvent.setup();
    renderChatPage();

    const composer = await screen.findByLabelText(/ask a question/i);
    await user.click(composer);
    await user.paste("[mock:fallback] explain why the answer is uncertain");
    await user.click(screen.getByRole("button", { name: /send/i }));

    expect(await screen.findByText(/low confidence/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/no sources were used for this response/i)).toBeInTheDocument();
    });
  });
});
