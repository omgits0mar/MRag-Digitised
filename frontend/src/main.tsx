import { renderApplication } from "@/bootstrap";
import { logger } from "@/lib/logger";
import "@/styles/globals.css";

async function startMockWorker(): Promise<void> {
  if (import.meta.env.VITE_ENABLE_MOCK !== "true") {
    return;
  }

  const { worker } = await import("./mocks/browser");
  await worker.start({
    onUnhandledRequest: "warn",
    serviceWorker: {
      url: "/mockServiceWorker.js",
    },
  });

  logger.info("mock.enabled", {
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "unset",
  });
}

async function renderApp(): Promise<void> {
  const rootElement = document.getElementById("root");
  if (rootElement === null) {
    throw new Error("Missing root element.");
  }

  await startMockWorker();
  renderApplication(rootElement, import.meta.env);
}

void renderApp();
