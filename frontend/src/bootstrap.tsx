import React from "react";
import ReactDOM from "react-dom/client";

import App from "@/App";
import { EnvBanner } from "@/components/layout/EnvBanner";
import { ConfigError, loadConfig, setConfigForTests } from "@/config";
import { logger } from "@/lib/logger";

export function createBootstrapElement(env: ImportMetaEnv): JSX.Element {
  try {
    const config = loadConfig(env);
    setConfigForTests(config);
    return <App />;
  } catch (error) {
    setConfigForTests(null);

    const message =
      error instanceof ConfigError
        ? error.message
        : "Frontend configuration could not be loaded.";

    logger.error("app.bootstrap.failed", {
      message,
    });

    return <EnvBanner message={message} />;
  }
}

export function renderApplication(rootElement: HTMLElement, env: ImportMetaEnv): void {
  const root = ReactDOM.createRoot(rootElement);

  root.render(
    <React.StrictMode>
      {createBootstrapElement(env)}
    </React.StrictMode>,
  );
}
