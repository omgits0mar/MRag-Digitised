import { ConfigError } from "@/config";

import {
  getApiClient,
  getConfigErrorResult,
  isApiError,
} from "./client";
import type {
  AnalyticsResponse,
  ApiResult,
  ConversationDetail,
  ConversationSummary,
  EvaluateRequest,
  EvaluateResponse,
  HealthResponse,
  ModelInfo,
  QuestionRequest,
  QuestionResponse,
  UploadResponse,
  UploadStatusResponse,
} from "./types";

interface RequestOptions {
  signal?: AbortSignal;
}

interface UploadRequestOptions extends RequestOptions {
  onProgress?: (percent: number) => void;
}

function toRequestConfig(opts?: RequestOptions): RequestOptions | undefined {
  if (opts?.signal === undefined) {
    return undefined;
  }

  return {
    signal: opts.signal,
  };
}

async function runRequest<T>(
  executor: () => Promise<T>,
): Promise<ApiResult<T>> {
  try {
    const data = await executor();
    return {
      kind: "ok",
      data,
    };
  } catch (error) {
    if (error instanceof ConfigError) {
      return getConfigErrorResult(error);
    }

    if (isApiError(error)) {
      return {
        kind: "error",
        error,
      };
    }

    return {
      kind: "error",
      error: {
        kind: "network",
        message: "Backend is unreachable.",
      },
    };
  }
}

export function getHealth(opts?: RequestOptions): Promise<ApiResult<HealthResponse>> {
  return runRequest<HealthResponse>(async () => {
    const response = await getApiClient().get<HealthResponse>("/health", toRequestConfig(opts));

    return response.data;
  });
}

export function askQuestion(
  request: QuestionRequest,
  opts?: RequestOptions,
): Promise<ApiResult<QuestionResponse>> {
  return runRequest<QuestionResponse>(async () => {
    const response = await getApiClient().post<QuestionResponse>(
      "/ask-question",
      request,
      toRequestConfig(opts),
    );

    return response.data;
  });
}

export function listConversations(
  opts?: RequestOptions,
): Promise<ApiResult<ConversationSummary[]>> {
  return runRequest<ConversationSummary[]>(async () => {
    const response = await getApiClient().get<ConversationSummary[]>(
      "/conversations",
      toRequestConfig(opts),
    );

    return response.data;
  });
}

export function getConversation(
  id: string,
  opts?: RequestOptions,
): Promise<ApiResult<ConversationDetail>> {
  return runRequest<ConversationDetail>(async () => {
    const response = await getApiClient().get<ConversationDetail>(
      `/conversations/${id}`,
      toRequestConfig(opts),
    );

    return response.data;
  });
}

export function deleteConversation(
  id: string,
  opts?: RequestOptions,
): Promise<ApiResult<void>> {
  return runRequest<void>(async () => {
    await getApiClient().delete(`/conversations/${id}`, toRequestConfig(opts));
  });
}

export function getAnalytics(
  range: { start: string; end: string },
  opts?: RequestOptions,
): Promise<ApiResult<AnalyticsResponse>> {
  return runRequest<AnalyticsResponse>(async () => {
    const response = await getApiClient().get<AnalyticsResponse>("/analytics", {
      params: {
        start_date: range.start,
        end_date: range.end,
      },
      ...(toRequestConfig(opts) ?? {}),
    });

    return response.data;
  });
}

export function runEvaluation(
  request: EvaluateRequest,
  opts?: RequestOptions,
): Promise<ApiResult<EvaluateResponse>> {
  return runRequest<EvaluateResponse>(async () => {
    const response = await getApiClient().post<EvaluateResponse>(
      "/evaluate",
      request,
      toRequestConfig(opts),
    );

    return response.data;
  });
}

export function listModels(opts?: RequestOptions): Promise<ApiResult<ModelInfo[]>> {
  return runRequest<ModelInfo[]>(async () => {
    const response = await getApiClient().get<ModelInfo[]>("/models", toRequestConfig(opts));

    return response.data;
  });
}

export function uploadFile(
  file: File,
  opts?: UploadRequestOptions,
): Promise<ApiResult<UploadResponse>> {
  return runRequest<UploadResponse>(async () => {
    const form = new FormData();
    form.append("file", file, file.name);

    const onProgress = opts?.onProgress;
    const response = await getApiClient().post<UploadResponse>("/upload", form, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      ...(opts?.signal === undefined ? {} : { signal: opts.signal }),
      ...(onProgress === undefined
        ? {}
        : {
            onUploadProgress: (event) => {
              if (event.total === undefined || event.total === 0) {
                return;
              }
              const percent = Math.round((event.loaded / event.total) * 100);
              onProgress(percent);
            },
          }),
    });

    return response.data;
  });
}

export function getUploadStatus(
  opts?: RequestOptions,
): Promise<ApiResult<UploadStatusResponse>> {
  return runRequest<UploadStatusResponse>(async () => {
    const response = await getApiClient().get<UploadStatusResponse>(
      "/upload/status",
      toRequestConfig(opts),
    );

    return response.data;
  });
}
