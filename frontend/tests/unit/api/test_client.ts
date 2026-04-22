import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from "axios";
import { describe, expect, it } from "vitest";

import { createRequestHandle, toApiError } from "@/api/client";

function collectSourceFiles(rootDir: string): string[] {
  const entries = readdirSync(rootDir, {
    withFileTypes: true,
  });

  return entries.flatMap((entry) => {
    const absolutePath = path.join(rootDir, entry.name);

    if (entry.isDirectory()) {
      return collectSourceFiles(absolutePath);
    }

    if (!absolutePath.endsWith(".ts") && !absolutePath.endsWith(".tsx")) {
      return [];
    }

    return [absolutePath];
  });
}

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

  it("keeps fetch isolated to the streaming transport seam", () => {
    const currentDir = path.dirname(fileURLToPath(import.meta.url));
    const srcDir = path.resolve(currentDir, "../../../src");
    const files = collectSourceFiles(srcDir);
    const filesUsingFetch = files.filter((filePath) =>
      readFileSync(filePath, "utf8").includes("fetch("),
    );

    expect(filesUsingFetch).toEqual([
      path.resolve(srcDir, "api/streaming.ts"),
    ]);
  });
});
