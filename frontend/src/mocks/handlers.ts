import { delay, http, HttpResponse } from "msw";

import type {
  QuestionRequest,
  StreamEvent,
  UploadResponse,
  UploadStatusResponse,
} from "@/api/types";

import {
  createStreamEvents,
  getConversationDetailById,
  listConversationSummaries,
  MOCK_DELAY_MS,
  MOCK_STREAM_DELAY_MS,
  MOCK_TIMEOUT_MS,
  persistMockExchange,
  prepareMockResponse,
  removeConversation,
  resetMockData,
  sampleAnalytics,
  sampleEvaluateResponse,
  sampleHealthOk,
  sampleModels,
} from "./data";

const encoder = new TextEncoder();

const DEFAULT_UPLOAD_ALLOWED = ["csv", "txt", "pdf", "md", "docx"];
const DEFAULT_UPLOAD_MAX_BYTES = 100 * 1024 * 1024;

const mockUploadStore: { totalVectors: number; lastUpload: UploadResponse | null } = {
  totalVectors: 0,
  lastUpload: null,
};

function resetMockUploads(): void {
  mockUploadStore.totalVectors = 0;
  mockUploadStore.lastUpload = null;
}

function getExtension(filename: string): string {
  const idx = filename.lastIndexOf(".");
  return idx === -1 ? "" : filename.slice(idx + 1).toLowerCase();
}

function serializeEvent(event: StreamEvent): Uint8Array {
  return encoder.encode(`data: ${JSON.stringify(event)}\n\n`);
}

function createStreamResponse(
  request: QuestionRequest,
): HttpResponse<ReadableStream<Uint8Array>> {
  const { events, response, scenario } = createStreamEvents(request);

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      try {
        for (const event of events) {
          if (scenario === "interrupt" && event.type === "done") {
            controller.error(new Error("Mock stream interrupted."));
            return;
          }

          controller.enqueue(serializeEvent(event));
          await delay(MOCK_STREAM_DELAY_MS);
        }

        persistMockExchange(request, response);
        controller.close();
      } catch (error) {
        controller.error(error);
      }
    },
  });

  return new HttpResponse<ReadableStream<Uint8Array>>(stream, {
    headers: {
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "Content-Type": "text/event-stream",
    },
  });
}

export const handlers = [
  http.get("*/health", async () => {
    await delay(MOCK_DELAY_MS);
    return HttpResponse.json(sampleHealthOk);
  }),
  http.post("*/ask-question", async ({ request }) => {
    const body = (await request.json()) as QuestionRequest;
    const { response, scenario } = prepareMockResponse(body);

    if (scenario === "timeout") {
      await delay(MOCK_TIMEOUT_MS);
      persistMockExchange(body, response);
      return HttpResponse.json(response);
    }

    await delay(MOCK_DELAY_MS);

    if (scenario === "error") {
      return HttpResponse.json(
        {
          detail: "The mock backend rejected this request.",
          error: "Mock backend error",
          status_code: 500,
        },
        {
          status: 500,
        },
      );
    }

    persistMockExchange(body, response);
    return HttpResponse.json(response);
  }),
  http.post("*/ask-question/stream", async ({ request }) => {
    const body = (await request.json()) as QuestionRequest;
    const { scenario } = prepareMockResponse(body);

    if (scenario === "timeout") {
      await delay(MOCK_TIMEOUT_MS);
      return createStreamResponse(body);
    }

    if (scenario === "error") {
      await delay(MOCK_DELAY_MS);
      return HttpResponse.json(
        {
          detail: "The mock streaming endpoint failed.",
          error: "Mock stream failure",
          status_code: 500,
        },
        {
          status: 500,
        },
      );
    }

    await delay(MOCK_DELAY_MS);
    return createStreamResponse(body);
  }),
  http.get("*/conversations", async () => {
    await delay(MOCK_DELAY_MS);
    return HttpResponse.json(listConversationSummaries());
  }),
  http.get("*/conversations/:id", async ({ params }) => {
    await delay(MOCK_DELAY_MS);

    const conversationId = String(params.id);
    const detail = getConversationDetailById(conversationId);

    if (detail === null) {
      return HttpResponse.json(
        {
          detail: `Conversation ${conversationId} was not found.`,
          error: "Not Found",
          status_code: 404,
        },
        {
          status: 404,
        },
      );
    }

    return HttpResponse.json(detail);
  }),
  http.delete("*/conversations/:id", async ({ params }) => {
    await delay(MOCK_DELAY_MS);

    const removed = removeConversation(String(params.id));
    if (!removed) {
      return HttpResponse.json(
        {
          detail: `Conversation ${String(params.id)} was not found.`,
          error: "Not Found",
          status_code: 404,
        },
        {
          status: 404,
        },
      );
    }

    return new HttpResponse(null, {
      status: 204,
    });
  }),
  http.get("*/analytics", async () => {
    await delay(MOCK_DELAY_MS);
    return HttpResponse.json(sampleAnalytics);
  }),
  http.post("*/evaluate", async () => {
    await delay(MOCK_DELAY_MS);
    return HttpResponse.json(sampleEvaluateResponse);
  }),
  http.get("*/models", async () => {
    await delay(MOCK_DELAY_MS);
    return HttpResponse.json(sampleModels);
  }),
  http.post("*/upload", async ({ request }) => {
    const form = await request.formData();
    const file = form.get("file");

    if (!(file instanceof File)) {
      return HttpResponse.json(
        {
          detail: "No file was uploaded.",
          error: "Bad Request",
          status_code: 400,
        },
        { status: 400 },
      );
    }

    const extension = getExtension(file.name);
    if (!DEFAULT_UPLOAD_ALLOWED.includes(extension)) {
      return HttpResponse.json(
        {
          detail: `Unsupported extension .${extension}.`,
          error: "Unsupported Media Type",
          status_code: 415,
        },
        { status: 415 },
      );
    }

    if (file.size > DEFAULT_UPLOAD_MAX_BYTES) {
      return HttpResponse.json(
        {
          detail: "Uploaded file exceeds the configured size cap.",
          error: "Payload Too Large",
          status_code: 413,
        },
        { status: 413 },
      );
    }

    await delay(MOCK_DELAY_MS);

    const chunksAdded = Math.max(1, Math.ceil(file.size / 1024));
    mockUploadStore.totalVectors += chunksAdded;
    const response: UploadResponse = {
      filename: file.name,
      extension,
      chunks_added: chunksAdded,
      total_vectors: mockUploadStore.totalVectors,
      ingested_at: Date.now() / 1000,
    };
    mockUploadStore.lastUpload = response;

    return HttpResponse.json(response, { status: 201 });
  }),
  http.get("*/upload/status", async () => {
    await delay(MOCK_DELAY_MS);
    const status: UploadStatusResponse = {
      total_vectors: mockUploadStore.totalVectors,
      allowed_extensions: DEFAULT_UPLOAD_ALLOWED,
      max_bytes: DEFAULT_UPLOAD_MAX_BYTES,
      last_upload: mockUploadStore.lastUpload,
    };
    return HttpResponse.json(status);
  }),
];

export { resetMockData, resetMockUploads };
