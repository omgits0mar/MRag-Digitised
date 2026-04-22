import { afterEach, describe, expect, it, vi } from "vitest";

import { setConfigForTests } from "@/config";
import { isStreamingUnsupported, parseSseChunk, streamAnswer } from "@/api/streaming";

describe("streaming transport", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("parses buffered SSE chunks and preserves trailing partial data", () => {
    const parsed = parseSseChunk(
      'data: {"type":"start","conversation_id":"conv-1"}\n\n' +
        'data: {"type":"token","content":"hello"}\n\n' +
        'data: {"type":"token"',
    );

    expect(parsed.events).toEqual([
      {
        type: "start",
        conversation_id: "conv-1",
      },
      {
        type: "token",
        content: "hello",
      },
    ]);
    expect(parsed.remainder).toBe('data: {"type":"token"');
  });

  it("maps unsupported stream endpoints so the caller can fall back", async () => {
    setConfigForTests({
      apiBaseUrl: "http://localhost:8000",
      apiRequestTimeoutMs: 500,
      defaultModel: "test-model",
      enableMock: false,
      enableStreaming: true,
    });

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: "missing",
            error: "Not Found",
            status_code: 404,
          }),
          {
            headers: {
              "Content-Type": "application/json",
            },
            status: 404,
          },
        ),
      ),
    );

    const result = await streamAnswer({
      question: "test",
    });

    expect(result.kind).toBe("error");
    if (result.kind === "error") {
      expect(isStreamingUnsupported(result.error)).toBe(true);
    }
  });
});
