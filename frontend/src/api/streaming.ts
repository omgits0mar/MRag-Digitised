import { getConfig } from "@/config";

import type {
  ApiError,
  ApiResult,
  BackendErrorEnvelope,
  QuestionRequest,
  QuestionResponse,
  StreamEvent,
} from "./types";

const decoder = new TextDecoder();

interface StreamAnswerOptions {
  signal?: AbortSignal;
  timeoutMs?: number;
  onEvent?: (event: StreamEvent) => void;
}

interface ParsedSseChunk {
  events: StreamEvent[];
  remainder: string;
}

function isBackendErrorEnvelope(value: unknown): value is BackendErrorEnvelope {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.error === "string" &&
    typeof candidate.detail === "string" &&
    typeof candidate.status_code === "number"
  );
}

function toResponseError(status: number, payload: unknown): ApiError {
  if (isBackendErrorEnvelope(payload)) {
    return {
      kind: "backend_error",
      status,
      message: payload.error,
      detail: payload.detail,
    };
  }

  return {
    kind: "backend_error",
    status,
    message: `Streaming request failed with HTTP ${status}.`,
    detail: "The streaming endpoint returned an unexpected payload.",
  };
}

function toStreamAbortError(reason: "timeout" | "cancelled"): ApiError {
  if (reason === "timeout") {
    return {
      kind: "timeout",
      message: "Request timed out.",
    };
  }

  return {
    kind: "cancelled",
    message: "Request was cancelled.",
  };
}

function createAbortController(
  signal: AbortSignal | undefined,
  timeoutMs: number,
): {
  signal: AbortSignal;
  cleanup: () => void;
  getAbortReason: () => "timeout" | "cancelled" | null;
} {
  const controller = new AbortController();
  let abortReason: "timeout" | "cancelled" | null = null;

  const handleExternalAbort = (): void => {
    abortReason = "cancelled";
    controller.abort();
  };

  if (signal !== undefined) {
    if (signal.aborted) {
      abortReason = "cancelled";
      controller.abort();
    } else {
      signal.addEventListener("abort", handleExternalAbort, { once: true });
    }
  }

  const timeoutId = window.setTimeout(() => {
    abortReason = "timeout";
    controller.abort();
  }, timeoutMs);

  return {
    signal: controller.signal,
    cleanup: () => {
      window.clearTimeout(timeoutId);
      signal?.removeEventListener("abort", handleExternalAbort);
    },
    getAbortReason: () => abortReason,
  };
}

export function parseSseChunk(buffer: string): ParsedSseChunk {
  const events: StreamEvent[] = [];
  const parts = buffer.split("\n\n");
  const remainder = parts.pop() ?? "";

  for (const part of parts) {
    const dataLines = part
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trim());

    if (dataLines.length === 0) {
      continue;
    }

    const payload = JSON.parse(dataLines.join("\n")) as StreamEvent;
    events.push(payload);
  }

  return {
    events,
    remainder,
  };
}

export function isStreamingUnsupported(error: ApiError): boolean {
  return error.kind === "backend_error" && [404, 405, 501].includes(error.status);
}

export async function streamAnswer(
  request: QuestionRequest,
  options: StreamAnswerOptions = {},
): Promise<ApiResult<QuestionResponse>> {
  const config = getConfig();
  const controller = createAbortController(
    options.signal,
    options.timeoutMs ?? config.apiRequestTimeoutMs,
  );

  try {
    const response = await fetch(`${config.apiBaseUrl}/ask-question/stream`, {
      body: JSON.stringify(request),
      headers: {
        Accept: "text/event-stream",
        "Content-Type": "application/json",
      },
      method: "POST",
      signal: controller.signal,
    });

    if (!response.ok) {
      let payload: unknown = null;
      try {
        payload = await response.json();
      } catch {
        payload = null;
      }

      return {
        kind: "error",
        error: toResponseError(response.status, payload),
      };
    }

    if (response.body === null) {
      return {
        kind: "error",
        error: {
          kind: "network",
          message: "Streaming response body was empty.",
        },
      };
    }

    const reader = response.body.getReader();
    let buffer = "";
    let finalResponse: QuestionResponse | null = null;

    let done = false;
    while (!done) {
      const chunk = await reader.read();
      done = chunk.done;
      if (done) {
        break;
      }

      const { value } = chunk;
      buffer += decoder.decode(value, { stream: true });
      const parsed = parseSseChunk(buffer);
      buffer = parsed.remainder;

      for (const event of parsed.events) {
        options.onEvent?.(event);

        if (event.type === "error") {
          return {
            kind: "error",
            error: {
              kind: "backend_error",
              status: event.error.status_code,
              message: event.error.error,
              detail: event.error.detail,
            },
          };
        }

        if (event.type === "done") {
          finalResponse = event.response;
        }
      }
    }

    if (buffer.trim() !== "") {
      const parsed = parseSseChunk(`${buffer}\n\n`);
      for (const event of parsed.events) {
        options.onEvent?.(event);
        if (event.type === "done") {
          finalResponse = event.response;
        }
      }
    }

    if (finalResponse === null) {
      return {
        kind: "error",
        error: {
          kind: "network",
          message: "Streaming response ended before completion.",
        },
      };
    }

    return {
      kind: "ok",
      data: finalResponse,
    };
  } catch {
    if (controller.signal.aborted) {
      return {
        kind: "error",
        error: toStreamAbortError(controller.getAbortReason() ?? "cancelled"),
      };
    }

    return {
      kind: "error",
      error: {
        kind: "network",
        message: "Backend is unreachable.",
      },
    };
  } finally {
    controller.cleanup();
  }
}
