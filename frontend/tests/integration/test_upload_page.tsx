import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";

import { setConfigForTests } from "@/config";
import { routes } from "@/router";

function renderUploadPage() {
  const router = createMemoryRouter(routes, {
    initialEntries: ["/upload"],
  });

  return render(<RouterProvider router={router} />);
}

describe("Upload page", () => {
  beforeEach(() => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1440,
      writable: true,
    });

    setConfigForTests({
      apiBaseUrl: "http://localhost:8000",
      apiRequestTimeoutMs: 5_000,
      defaultModel: "llama-3.1-8b-instant",
      enableMock: true,
      enableStreaming: false,
    });
  });

  it("renders accepted formats and index status from the backend", async () => {
    renderUploadPage();

    expect(
      await screen.findByRole("heading", { name: /expand the knowledge base/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/\.csv, \.txt, \.pdf, \.md, \.docx/i)).toBeInTheDocument();
  });

  it("uploads a valid file and shows it in the session list", async () => {
    const user = userEvent.setup();
    renderUploadPage();

    await screen.findByRole("heading", { name: /expand the knowledge base/i });

    const input = screen.getByLabelText(/select file to upload/i) as HTMLInputElement;
    const file = new File(["The capital of Burkina Faso is Ouagadougou."], "facts.txt", {
      type: "text/plain",
    });

    await user.upload(input, file);

    await waitFor(() => {
      expect(screen.getByText("facts.txt")).toBeInTheDocument();
    });
    expect(screen.getByText(/index now \d+ vectors/i)).toBeInTheDocument();
  });

  it("rejects files with an unsupported extension client-side", async () => {
    const user = userEvent.setup();
    renderUploadPage();

    await screen.findByRole("heading", { name: /expand the knowledge base/i });

    const input = screen.getByLabelText(/select file to upload/i) as HTMLInputElement;
    const file = new File(["bad"], "malware.exe", { type: "application/octet-stream" });

    await user.upload(input, file);

    expect(await screen.findByRole("alert")).toHaveTextContent(/unsupported file type/i);
  });
});
