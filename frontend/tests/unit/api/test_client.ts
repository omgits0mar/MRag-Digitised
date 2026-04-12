import { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from "axios";
import { describe, expect, it } from "vitest";

import { createRequestHandle, toApiError } from "@/api/client";

describe("api client error normalization", () => {
  it("maps timeout failures to timeout errors", () => {
    const error = new AxiosError("timeout", "ECONNABORTED");

    expect(toApiError(error)).toEqual({
      kind: "timeout",
      message: "Request timed out.",
    });
  });

  it("maps cancelled requests to cancelled errors", () => {
    const error = new AxiosError("cancelled", "ERR_CANCELED");

    expect(toApiError(error)).toEqual({
      kind: "cancelled",
      message: "Request was cancelled.",
    });
  });

  it("maps backend envelopes to backend_error results", () => {
    const response: AxiosResponse = {
      config: {
        headers: {},
      } as InternalAxiosRequestConfig,
      data: {
        error: "Validation failed",
        detail: "question is required",
        status_code: 422,
      },
      headers: {},
      status: 422,
      statusText: "Unprocessable Entity",
    };

    const error = new AxiosError(
      "backend failure",
      AxiosError.ERR_BAD_RESPONSE,
      undefined,
      undefined,
      response,
    );

    expect(toApiError(error)).toEqual({
      kind: "backend_error",
      status: 422,
      message: "Validation failed",
      detail: "question is required",
    });
  });

  it("creates cancellable request handles", () => {
    const handle = createRequestHandle();

    expect(handle.signal.aborted).toBe(false);
    handle.cancel();
    expect(handle.signal.aborted).toBe(true);
  });
});
