import axe from "axe-core";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { routes } from "@/router";

function renderShell(initialEntries: string[] = ["/"]) {
  const router = createMemoryRouter(routes, {
    initialEntries,
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

describe("App shell", () => {
  it("renders shell navigation and the default content view on desktop", async () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1280,
      writable: true,
    });

    const { container } = renderShell();

    expect(await screen.findByRole("heading", { name: /multilingual rag platform/i })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: /main navigation/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Chat" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "History" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /open navigation menu/i })).not.toBeInTheDocument();

    await assertNoCriticalAxeViolations(container);
  });

  it("opens the navigation drawer on small screens with proper dialog semantics", async () => {
    const user = userEvent.setup();
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 360,
      writable: true,
    });

    const { container } = renderShell();

    const toggleButton = await screen.findByRole("button", { name: /open navigation menu/i });
    expect(toggleButton).toHaveAttribute("aria-expanded", "false");
    expect(toggleButton).toHaveAttribute("aria-controls", "app-shell-sidebar");
    expect(screen.queryByRole("navigation", { name: /main navigation/i })).not.toBeInTheDocument();

    await user.click(toggleButton);

    const drawer = screen.getByRole("dialog");
    expect(drawer).toHaveAttribute("aria-modal", "true");
    expect(drawer).toHaveAttribute("id", "app-shell-sidebar");
    expect(toggleButton).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("navigation", { name: /main navigation/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /close navigation menu/i })).toBeInTheDocument();

    await assertNoCriticalAxeViolations(container);

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
