import { useEffect, useState } from "react";

import { createRequestHandle } from "@/api/client";
import { getHealth } from "@/api/endpoints";

function toHealthLabel(result: Awaited<ReturnType<typeof getHealth>>): string {
  if (result.kind === "error") {
    switch (result.error.kind) {
      case "backend_error":
        return `Backend error ${result.error.status}`;
      case "timeout":
        return "Health check timed out";
      case "cancelled":
        return "Health check cancelled";
      case "not_configured":
        return "Configuration missing";
      case "network":
      default:
        return "Backend unreachable";
    }
  }

  switch (result.data.status) {
    case "healthy":
      return "Backend healthy";
    case "degraded":
      return "Backend degraded";
    case "not_ready":
    default:
      return "Backend not ready";
  }
}

export function useHealthCheck(): string {
  const [label, setLabel] = useState("Health check pending");

  useEffect(() => {
    const handle = createRequestHandle();
    void getHealth({ signal: handle.signal }).then((result) => {
      setLabel(toHealthLabel(result));
    });

    return () => {
      handle.cancel();
    };
  }, []);

  return label;
}
