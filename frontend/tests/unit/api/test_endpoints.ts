import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "@/api/client";
import { askQuestion, getAnalytics, getHealth } from "@/api/endpoints";
import { setConfigForTests } from "@/config";

function createResponse<T>(data: T): AxiosResponse<T> {
  return {
    data,
    headers: {},
    status: 200,
    statusText: "OK",
    config: {
      headers: {},
    } as InternalAxiosRequestConfig,
  };
}

describe("API endpoints", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    setConfigForTests({
      apiBaseUrl: "http://localhost:8000",
      enableMock: false,
      defaultModel: "test-model",
      enableStreaming: false,
      apiRequestTimeoutMs: 30_000,
    });
  });

  it("wraps health responses in ApiResult.ok", async () => {
    vi.spyOn(apiClient, "get").mockResolvedValueOnce(
      createResponse({
        status: "healthy",
        vector_store: "loaded",
        llm_provider: "reachable",
        database: "connected",
        uptime_seconds: 12,
        persistence_failure_count: 0,
      }),
    );

    await expect(getHealth()).resolves.toEqual({
      kind: "ok",
      data: {
        status: "healthy",
        vector_store: "loaded",
        llm_provider: "reachable",
        database: "connected",
        uptime_seconds: 12,
        persistence_failure_count: 0,
      },
    });
  });

  it("posts the ask-question payload without changing field names", async () => {
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce(
      createResponse({
        answer: "answer",
        confidence_score: 0.8,
        is_fallback: false,
        sources: [],
        response_time_ms: 10,
        conversation_id: "conv-1",
      }),
    );

    await askQuestion({
      question: "What is MRAG?",
      conversation_id: "conv-1",
      expand: true,
      temperature: 0.2,
      max_tokens: 400,
    });

    expect(postSpy).toHaveBeenCalledWith(
      "/ask-question",
      {
        question: "What is MRAG?",
        conversation_id: "conv-1",
        expand: true,
        temperature: 0.2,
        max_tokens: 400,
      },
      undefined,
    );
  });

  it("sends analytics range params using backend query names", async () => {
    const getSpy = vi.spyOn(apiClient, "get").mockResolvedValueOnce(
      createResponse({
        total_queries: 1,
        avg_latency_ms: 1,
        cache_hit_rate: 0.5,
        top_domains: [],
        queries_per_day: {},
      }),
    );

    await getAnalytics({
      start: "2026-04-01T00:00:00+00:00",
      end: "2026-04-12T00:00:00+00:00",
    });

    expect(getSpy).toHaveBeenCalledWith("/analytics", {
      params: {
        start_date: "2026-04-01T00:00:00+00:00",
        end_date: "2026-04-12T00:00:00+00:00",
      },
      signal: undefined,
    });
  });
});
