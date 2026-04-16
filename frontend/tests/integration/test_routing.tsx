import { cleanup, render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { routes } from "@/router";

describe("App routing", () => {
  it("renders each top-level route through direct deep links", async () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1280,
      writable: true,
    });

    const chatRouter = createMemoryRouter(routes, {
      initialEntries: ["/"],
    });

    render(<RouterProvider router={chatRouter} />);

    expect(
      await screen.findByRole("heading", {
        name: /ask multilingual questions with confidence/i,
      }),
    ).toBeInTheDocument();
    expect(chatRouter.state.location.pathname).toBe("/");

    cleanup();

    const historyRouter = createMemoryRouter(routes, {
      initialEntries: ["/history"],
    });

    render(<RouterProvider router={historyRouter} />);
    expect(
      await screen.findByRole("heading", {
        name: /conversation history is wired to shared state/i,
      }),
    ).toBeInTheDocument();
    expect(historyRouter.state.location.pathname).toBe("/history");

    cleanup();

    const settingsRouter = createMemoryRouter(routes, {
      initialEntries: ["/settings"],
    });

    render(<RouterProvider router={settingsRouter} />);
    expect(
      await screen.findByRole("heading", {
        name: /preferences already persist across reloads/i,
      }),
    ).toBeInTheDocument();
    expect(settingsRouter.state.location.pathname).toBe("/settings");
  });
});
