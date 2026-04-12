import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { createBootstrapElement } from "@/bootstrap";

describe("bootstrap environment validation", () => {
  it("renders an actionable banner when the API base URL is missing", () => {
    render(
      createBootstrapElement({
        BASE_URL: "/",
        DEV: false,
        MODE: "test",
        PROD: false,
        SSR: false,
        VITE_DEFAULT_MODEL: "test-model",
        VITE_ENABLE_MOCK: "false",
        VITE_ENABLE_STREAMING: "false",
        VITE_API_REQUEST_TIMEOUT_MS: "30000",
      } as ImportMetaEnv),
    );

    expect(screen.getByRole("heading", { name: /frontend configuration is incomplete/i })).toBeInTheDocument();
    expect(screen.getByText(/set `vite_api_base_url` in `frontend\/.env`/i)).toBeInTheDocument();
  });
});
