import { delay, http, HttpResponse } from "msw";

import type { QuestionRequest } from "@/api/types";

import {
  sampleAnalytics,
  sampleConversationDetails,
  sampleConversationSummaries,
  sampleEvaluateResponse,
  sampleHealthOk,
  sampleModels,
  sampleQuestionResponse,
} from "./data";

const MOCK_DELAY_MS = 80;

export const handlers = [
  http.get("*/health", async () => {
    await delay(MOCK_DELAY_MS);
    return HttpResponse.json(sampleHealthOk);
  }),
  http.post("*/ask-question", async ({ request }) => {
    const body = (await request.json()) as QuestionRequest;

    await delay(MOCK_DELAY_MS);
    return HttpResponse.json({
      ...sampleQuestionResponse,
      answer: `Mock answer for: ${body.question}`,
      conversation_id: body.conversation_id ?? sampleQuestionResponse.conversation_id,
    });
  }),
  http.get("*/conversations", async () => {
    await delay(MOCK_DELAY_MS);
    return HttpResponse.json(sampleConversationSummaries);
  }),
  http.get("*/conversations/:id", async ({ params }) => {
    await delay(MOCK_DELAY_MS);

    const conversationId = String(params.id);
    const detail = sampleConversationDetails[conversationId];

    if (detail === undefined) {
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
  http.delete("*/conversations/:id", async () => {
    await delay(MOCK_DELAY_MS);
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
];

