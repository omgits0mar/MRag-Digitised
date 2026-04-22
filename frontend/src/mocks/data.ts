import type {
  AnalyticsResponse,
  ConversationDetail,
  ConversationMessage,
  ConversationSummary,
  EvaluateResponse,
  HealthResponse,
  ModelInfo,
  QuestionRequest,
  QuestionResponse,
  SourceResponse,
  StreamEvent,
} from "@/api/types";
import { getConversationTitle } from "@/api/types";

export const MOCK_DELAY_MS = 80;
export const MOCK_STREAM_DELAY_MS = 40;
export const MOCK_TIMEOUT_MS = 5_000;

type MockScenario = "default" | "fallback" | "error" | "timeout" | "interrupt";

interface PreparedMockResponse {
  scenario: MockScenario;
  response: QuestionResponse;
  conversationId: string;
}

const SCENARIO_PATTERN = /\[mock:(fallback|error|timeout|interrupt)\]/i;

const sampleSources = [
  {
    chunk_id: "chunk-1",
    chunk_index: 1,
    doc_id: "doc-pipeline-001",
    domain_tag: "pipeline",
    original_answer: "Validated chunks improve downstream grounding.",
    original_question: "How does the MRAG pipeline work?",
    question_type: "process",
    relevance_score: 0.91,
    text: "Validated multilingual chunks move through ingestion, embedding, retrieval, and answer generation with explicit grounding.",
    total_chunks: 4,
  },
  {
    chunk_id: "chunk-2",
    chunk_index: 2,
    doc_id: "doc-retrieval-014",
    domain_tag: "retrieval",
    original_answer: "The retrieved chunks anchor the final answer.",
    original_question: "Why are citations important in RAG?",
    question_type: "why",
    relevance_score: 0.84,
    text: "The retriever ranks chunk candidates before the generator composes a cited answer.",
    total_chunks: 4,
  },
  {
    chunk_id: "chunk-3",
    chunk_index: 3,
    doc_id: "doc-latency-021",
    domain_tag: "operations",
    original_answer: "Latency is broken down by retrieval and generation stages.",
    original_question: "How do we monitor the system?",
    question_type: "metrics",
    relevance_score: 0.72,
    text: "Latency and cache-hit metrics are captured per answer so the UI can show retrieval, search, and generation timings.",
    total_chunks: 4,
  },
] satisfies SourceResponse[];

function createConversationMessage(
  message: Partial<ConversationMessage> & Pick<ConversationMessage, "id" | "role" | "content" | "created_at">,
): ConversationMessage {
  return {
    ...message,
    completed_at: message.completed_at ?? message.created_at,
  };
}

function createInitialConversations(): Record<string, ConversationDetail> {
  return {
    "conv-1": {
      created_at: "2026-04-10T08:30:00Z",
      id: "conv-1",
      message_count: 2,
      title: "Arabic policy translation review",
      updated_at: "2026-04-10T08:31:00Z",
      messages: [
        createConversationMessage({
          content: "Summarize the government circular in Modern Standard Arabic.",
          created_at: "2026-04-10T08:30:00Z",
          id: "msg-1",
          role: "user",
        }),
        createConversationMessage({
          confidence_score: 0.93,
          content:
            "## Arabic summary\n\nThe circular focuses on archival digitisation standards, metadata retention, and reviewer sign-off.[1]",
          created_at: "2026-04-10T08:31:00Z",
          id: "msg-2",
          is_fallback: false,
          latency: {
            cache_hit: true,
            generation_ms: 244,
            retrieval_ms: 118,
            search_ms: 66,
            total_ms: 428,
          },
          role: "assistant",
          sources: sampleSources.slice(0, 1),
          token_usage: {
            completion_tokens: 92,
            prompt_tokens: 221,
            total_tokens: 313,
          },
        }),
      ],
    },
    "conv-2": {
      created_at: "2026-04-09T11:15:00Z",
      id: "conv-2",
      message_count: 2,
      title: "Kurdish dataset quality pass",
      updated_at: "2026-04-09T11:16:00Z",
      messages: [
        createConversationMessage({
          content: "Show the weak retrieval cases in the Kurdish evaluation slice.",
          created_at: "2026-04-09T11:15:00Z",
          id: "msg-3",
          role: "user",
        }),
        createConversationMessage({
          confidence_score: 0.67,
          content:
            "Three low-confidence cases cluster around OCR-heavy historical scans, mostly where citations map to noisy chunks.[1][2]",
          created_at: "2026-04-09T11:16:00Z",
          id: "msg-4",
          is_fallback: false,
          latency: {
            generation_ms: 302,
            retrieval_ms: 140,
            search_ms: 78,
            total_ms: 520,
          },
          role: "assistant",
          sources: sampleSources.slice(0, 2),
          token_usage: {
            completion_tokens: 78,
            prompt_tokens: 176,
            total_tokens: 254,
          },
        }),
      ],
    },
    "conv-3": {
      created_at: "2026-04-08T14:05:00Z",
      id: "conv-3",
      message_count: 2,
      title: "Vector-store latency benchmark follow-up",
      updated_at: "2026-04-08T14:06:00Z",
      messages: [
        createConversationMessage({
          content: "Compare the latest query latency against the prior benchmark run.",
          created_at: "2026-04-08T14:05:00Z",
          id: "msg-5",
          role: "user",
        }),
        createConversationMessage({
          confidence_score: 0.88,
          content:
            "Median latency improved by 14% after the cache warm-up change, with the largest gain in retrieval/search time.[1][3]",
          created_at: "2026-04-08T14:06:00Z",
          id: "msg-6",
          is_fallback: false,
          latency: {
            cache_hit: true,
            generation_ms: 189,
            retrieval_ms: 96,
            search_ms: 41,
            total_ms: 326,
          },
          role: "assistant",
          sources: [sampleSources[0]!, sampleSources[2]!],
          token_usage: {
            completion_tokens: 64,
            prompt_tokens: 144,
            total_tokens: 208,
          },
        }),
      ],
    },
  };
}

let mockConversations = createInitialConversations();
let nextConversationNumber = 4;
let nextMessageNumber = 7;

function getScenario(question: string): MockScenario {
  const match = question.match(SCENARIO_PATTERN);
  if (match === null) {
    return "default";
  }

  switch (match[1]?.toLowerCase()) {
    case "fallback":
      return "fallback";
    case "error":
      return "error";
    case "timeout":
      return "timeout";
    case "interrupt":
      return "interrupt";
    default:
      return "default";
  }
}

function scrubScenarioTag(question: string): string {
  return question.replace(SCENARIO_PATTERN, "").trim();
}

function createAnswer(question: string, scenario: MockScenario): string {
  const plainQuestion = scrubScenarioTag(question) || "your latest question";

  if (scenario === "fallback") {
    return `The system can only provide a cautious answer for "${plainQuestion}" because the retriever did not return strong supporting evidence.`;
  }

  return [
    `## Response for ${plainQuestion}`,
    "",
    "1. Documents are ingested and validated before they are embedded.[1]",
    "2. The retriever ranks multilingual chunks that best support the question.[2]",
    "3. The generator answers from the ranked evidence and reports timing metadata.[3]",
    "",
    "Use `Retry` when a response is interrupted so the same prompt can be resubmitted safely.",
  ].join("\n");
}

function createResponse(question: string, conversationId: string): QuestionResponse {
  const scenario = getScenario(question);

  if (scenario === "fallback") {
    return {
      answer: createAnswer(question, scenario),
      confidence_score: 0.38,
      conversation_id: conversationId,
      is_fallback: true,
      latency: {
        generation_ms: 331,
        total_ms: 331,
      },
      token_usage: {
        completion_tokens: 51,
        prompt_tokens: 124,
        total_tokens: 175,
      },
    };
  }

  return {
    answer: createAnswer(question, scenario),
    confidence_score: 0.91,
    conversation_id: conversationId,
    is_fallback: false,
    latency: {
      cache_hit: scenario !== "interrupt",
      generation_ms: 241,
      retrieval_ms: 132,
      search_ms: 58,
      total_ms: 431,
    },
    response_time_ms: 431,
    sources: sampleSources,
    token_usage: {
      completion_tokens: 108,
      prompt_tokens: 226,
      total_tokens: 334,
    },
  };
}

function summarizeConversation(detail: ConversationDetail): ConversationSummary {
  return {
    created_at: detail.created_at,
    id: detail.id,
    message_count: detail.message_count,
    title: detail.title,
    updated_at: detail.updated_at,
  };
}

function cloneConversation(detail: ConversationDetail): ConversationDetail {
  return structuredClone(detail);
}

function ensureConversation(question: string, requestedConversationId?: string | null): string {
  if (requestedConversationId !== undefined && requestedConversationId !== null) {
    if (mockConversations[requestedConversationId] === undefined) {
      mockConversations[requestedConversationId] = {
        created_at: new Date().toISOString(),
        id: requestedConversationId,
        message_count: 0,
        title: getConversationTitle(scrubScenarioTag(question) || "New conversation"),
        updated_at: new Date().toISOString(),
        messages: [],
      };
    }

    return requestedConversationId;
  }

  const id = `conv-${nextConversationNumber}`;
  nextConversationNumber += 1;

  mockConversations[id] = {
    created_at: new Date().toISOString(),
    id,
    message_count: 0,
    title: getConversationTitle(scrubScenarioTag(question) || "New conversation"),
    updated_at: new Date().toISOString(),
    messages: [],
  };

  return id;
}

function nextMessageId(): string {
  const id = `msg-${nextMessageNumber}`;
  nextMessageNumber += 1;
  return id;
}

export function resetMockData(): void {
  mockConversations = createInitialConversations();
  nextConversationNumber = 4;
  nextMessageNumber = 7;
}

export function listConversationSummaries(): ConversationSummary[] {
  return Object.values(mockConversations)
    .map(summarizeConversation)
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at));
}

export function getConversationDetailById(id: string): ConversationDetail | null {
  const detail = mockConversations[id];
  return detail === undefined ? null : cloneConversation(detail);
}

export function removeConversation(id: string): boolean {
  if (mockConversations[id] === undefined) {
    return false;
  }

  delete mockConversations[id];
  return true;
}

export function prepareMockResponse(request: QuestionRequest): PreparedMockResponse {
  const conversationId = ensureConversation(request.question, request.conversation_id);
  return {
    conversationId,
    response: createResponse(request.question, conversationId),
    scenario: getScenario(request.question),
  };
}

export function persistMockExchange(
  request: QuestionRequest,
  response: QuestionResponse,
  options?: {
    assistantContent?: string;
    assistantCreatedAt?: string;
    userCreatedAt?: string;
  },
): ConversationDetail {
  const conversationId = response.conversation_id ?? ensureConversation(request.question, null);
  const detail = mockConversations[conversationId];
  if (detail === undefined) {
    throw new Error(`Mock conversation ${conversationId} is missing.`);
  }

  const userCreatedAt = options?.userCreatedAt ?? new Date().toISOString();
  const assistantCreatedAt = options?.assistantCreatedAt ?? new Date().toISOString();

  detail.messages.push(
    createConversationMessage({
      content: scrubScenarioTag(request.question),
      created_at: userCreatedAt,
      id: nextMessageId(),
      role: "user",
    }),
  );
  detail.messages.push(
    createConversationMessage({
      confidence_score: response.confidence_score,
      content: options?.assistantContent ?? response.answer,
      created_at: assistantCreatedAt,
      id: nextMessageId(),
      is_fallback: response.is_fallback,
      latency: response.latency,
      role: "assistant",
      sources: response.sources,
      token_usage: response.token_usage,
    }),
  );

  detail.message_count = detail.messages.length;
  detail.updated_at = assistantCreatedAt;
  if (detail.title.trim() === "") {
    detail.title = getConversationTitle(scrubScenarioTag(request.question));
  }

  return cloneConversation(detail);
}

export function createStreamEvents(request: QuestionRequest): {
  scenario: MockScenario;
  response: QuestionResponse;
  events: StreamEvent[];
} {
  const prepared = prepareMockResponse(request);
  const events: StreamEvent[] = [
    {
      type: "start",
      conversation_id: prepared.conversationId,
      created_at: new Date().toISOString(),
      request_id: crypto.randomUUID(),
    },
  ];

  const answer = prepared.response.answer;
  for (let index = 0; index < answer.length; index += 36) {
    events.push({
      type: "token",
      content: answer.slice(index, index + 36),
    });
  }

  events.push({
    type: "done",
    response: prepared.response,
  });

  return {
    events,
    response: prepared.response,
    scenario: prepared.scenario,
  };
}

export const sampleHealthOk = {
  database: "connected",
  llm_provider: "reachable",
  persistence_failure_count: 0,
  status: "healthy",
  uptime_seconds: 86_400,
  vector_store: "loaded",
} satisfies HealthResponse;

export const sampleAnalytics = {
  avg_latency_ms: 412,
  cache_hit_rate: 0.41,
  queries_per_day: {
    "2026-04-08": 12,
    "2026-04-09": 16,
    "2026-04-10": 19,
    "2026-04-11": 21,
    "2026-04-12": 17,
  },
  top_domains: ["pipeline", "retrieval", "operations"],
  total_queries: 85,
} satisfies AnalyticsResponse;

export const sampleEvaluateResponse = {
  benchmark: {
    p50_ms: 388,
    p95_ms: 742,
  },
  regressions: [],
  response_quality: {
    bleu: 0.47,
    rouge_l: 0.58,
  },
  retrieval: {
    mrr: 0.72,
    recall_at_5: 0.81,
  },
  total_queries: 128,
} satisfies EvaluateResponse;

export const sampleModels = [
  {
    description: "Fast-turnaround model for lightweight chat and health checks.",
    name: "llama-3.1-8b-instant",
    provider: "Groq",
    tier: "fast",
  },
  {
    description: "Balanced model for everyday multilingual retrieval questions.",
    name: "gpt-4.1-mini",
    provider: "OpenAI",
    tier: "balanced",
  },
  {
    description: "Higher-quality model for evaluation and complex analysis runs.",
    name: "gpt-4.1",
    provider: "OpenAI",
    tier: "quality",
  },
] satisfies ModelInfo[];
