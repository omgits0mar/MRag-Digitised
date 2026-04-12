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

describe("App shell", () => {
  it("renders shell navigation and the default content view on desktop", async () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1280,
      writable: true,
    });

    renderShell();

    expect(await screen.findByRole("heading", { name: /multilingual rag platform/i })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: /main navigation/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Chat" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "History" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /open navigation menu/i })).not.toBeInTheDocument();
  });

  it("opens the navigation drawer on small screens", async () => {
    const user = userEvent.setup();
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 360,
      writable: true,
    });

    renderShell();

    const toggleButton = await screen.findByRole("button", { name: /open navigation menu/i });
    expect(screen.queryByRole("navigation", { name: /main navigation/i })).not.toBeInTheDocument();

    await user.click(toggleButton);

    expect(screen.getByRole("navigation", { name: /main navigation/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "History" })).toBeInTheDocument();
  });
});
