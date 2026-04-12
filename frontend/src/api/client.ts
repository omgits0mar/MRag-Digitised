import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

import { ConfigError, getConfig } from "@/config";
import { logger } from "@/lib/logger";

import type { ApiError, BackendErrorEnvelope } from "./types";

interface RequestMetadata {
  correlationId: string;
  startedAt: number;
}

type InstrumentedRequestConfig = InternalAxiosRequestConfig & {
  metadata?: RequestMetadata;
};

export const apiClient: AxiosInstance = axios.create({
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
  withCredentials: false,
});

let interceptorsRegistered = false;

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

export function isApiError(value: unknown): value is ApiError {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return typeof candidate.kind === "string" && typeof candidate.message === "string";
}

export function createRequestHandle(): { signal: AbortSignal; cancel(): void } {
  const controller = new AbortController();

  return {
    signal: controller.signal,
    cancel(): void {
      controller.abort();
    },
  };
}

export function toApiError(error: unknown): ApiError {
  if (axios.isCancel(error)) {
    return {
      kind: "cancelled",
      message: "Request was cancelled.",
    };
  }

  if (!(error instanceof AxiosError)) {
    return {
      kind: "network",
      message: "Backend is unreachable.",
    };
  }

  if (error.code === "ERR_CANCELED") {
    return {
      kind: "cancelled",
      message: "Request was cancelled.",
    };
  }

  if (error.code === "ECONNABORTED") {
    return {
      kind: "timeout",
      message: "Request timed out.",
    };
  }

  if (error.response === undefined) {
    return {
      kind: "network",
      message: "Backend is unreachable.",
    };
  }

  if (isBackendErrorEnvelope(error.response.data)) {
    return {
      kind: "backend_error",
      status: error.response.status,
      message: error.response.data.error,
      detail: error.response.data.detail,
    };
  }

  return {
    kind: "network",
    message: `Unexpected response from backend (HTTP ${error.response.status}).`,
  };
}

function registerInterceptors(): void {
  if (interceptorsRegistered) {
    return;
  }

  apiClient.interceptors.request.use((config) => {
    const instrumentedConfig = config as InstrumentedRequestConfig;
    const correlationId = crypto.randomUUID();
    instrumentedConfig.metadata = {
      correlationId,
      startedAt: Date.now(),
    };
    instrumentedConfig.headers.set("X-Correlation-Id", correlationId);

    logger.debug("api.request", {
      correlationId,
      method: instrumentedConfig.method,
      url: instrumentedConfig.url,
    });

    return instrumentedConfig;
  });

  apiClient.interceptors.response.use(
    (response) => {
      const instrumentedConfig = response.config as InstrumentedRequestConfig;
      const durationMs =
        instrumentedConfig.metadata === undefined
          ? undefined
          : Date.now() - instrumentedConfig.metadata.startedAt;

      logger.debug("api.response", {
        correlationId: instrumentedConfig.metadata?.correlationId,
        durationMs,
        status: response.status,
        url: instrumentedConfig.url,
      });

      return response;
    },
    (error: unknown) => Promise.reject(toApiError(error)),
  );

  interceptorsRegistered = true;
}

export function getApiClient(): AxiosInstance {
  registerInterceptors();

  const config = getConfig();
  apiClient.defaults.baseURL = config.apiBaseUrl;
  apiClient.defaults.timeout = config.apiRequestTimeoutMs;

  return apiClient;
}

export function getConfigErrorResult(error: ConfigError): { kind: "error"; error: ApiError } {
  return {
    kind: "error",
    error: {
      kind: "not_configured",
      message: error.message,
    },
  };
}
