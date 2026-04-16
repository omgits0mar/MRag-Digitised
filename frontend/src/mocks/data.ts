import type {
  AnalyticsResponse,
  ConversationDetail,
  ConversationSummary,
  EvaluateResponse,
  HealthResponse,
  ModelInfo,
  QuestionResponse,
} from "@/api/types";

export const sampleHealthOk = {
  database: "connected",
  llm_provider: "reachable",
  persistence_failure_count: 0,
  status: "healthy",
  uptime_seconds: 86_400,
  vector_store: "loaded",
} satisfies HealthResponse;

export const sampleHealthDegraded = {
  ...sampleHealthOk,
  persistence_failure_count: 1,
  status: "degraded",
} satisfies HealthResponse;

export const sampleConversationSummaries = [
  {
    created_at: "2026-04-10T08:30:00Z",
    id: "conv-1",
    message_count: 4,
    title: "Arabic policy translation review",
    updated_at: "2026-04-10T08:45:00Z",
  },
  {
    created_at: "2026-04-09T11:15:00Z",
    id: "conv-2",
    message_count: 6,
    title: "Kurdish dataset quality pass",
    updated_at: "2026-04-09T11:48:00Z",
  },
  {
    created_at: "2026-04-08T14:05:00Z",
    id: "conv-3",
    message_count: 3,
    title: "Vector-store latency benchmark follow-up",
    updated_at: "2026-04-08T14:21:00Z",
  },
] satisfies ConversationSummary[];

const sampleConversationSummaryOne = sampleConversationSummaries[0]!;
const sampleConversationSummaryTwo = sampleConversationSummaries[1]!;
const sampleConversationSummaryThree = sampleConversationSummaries[2]!;

export const sampleConversationDetails: Record<string, ConversationDetail> = {
  "conv-1": {
    ...sampleConversationSummaryOne,
    messages: [
      {
        content: "Summarize the government circular in Modern Standard Arabic.",
        created_at: "2026-04-10T08:30:00Z",
        id: "msg-1",
        role: "user",
      },
      {
        content: "The circular focuses on archival digitisation requirements for 2026.",
        created_at: "2026-04-10T08:31:00Z",
        id: "msg-2",
        role: "assistant",
      },
    ],
  },
  "conv-2": {
    ...sampleConversationSummaryTwo,
    messages: [
      {
        content: "Show the weak retrieval cases in the Kurdish evaluation slice.",
        created_at: "2026-04-09T11:15:00Z",
        id: "msg-3",
        role: "user",
      },
      {
        content: "Three low-confidence cases cluster around OCR-heavy historical scans.",
        created_at: "2026-04-09T11:16:00Z",
        id: "msg-4",
        role: "assistant",
      },
    ],
  },
  "conv-3": {
    ...sampleConversationSummaryThree,
    messages: [
      {
        content: "Compare the latest query latency against the prior benchmark run.",
        created_at: "2026-04-08T14:05:00Z",
        id: "msg-5",
        role: "user",
      },
      {
        content: "Median latency improved by 14% after the cache warm-up change.",
        created_at: "2026-04-08T14:06:00Z",
        id: "msg-6",
        role: "assistant",
      },
    ],
  },
};

export const sampleQuestionResponse = {
  answer: "Mock mode is active and the frontend is using typed sample data.",
  confidence_score: 0.91,
  conversation_id: "conv-1",
  is_fallback: false,
  response_time_ms: 242,
  sources: [
    {
      chunk_id: "chunk-1",
      doc_id: "doc-policy-2026",
      relevance_score: 0.82,
      text: "Digitisation policy updates for archival processing in 2026.",
    },
    {
      chunk_id: "chunk-2",
      doc_id: "doc-eval-014",
      relevance_score: 0.58,
      text: "Evaluation notes covering OCR noise mitigation and relevance scoring.",
    },
    {
      chunk_id: "chunk-3",
      doc_id: "doc-ops-009",
      relevance_score: 0.33,
      text: "Operational guidance for monitoring latency and fallback conditions.",
    },
  ],
} satisfies QuestionResponse;

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
  top_domains: ["policy", "archives", "ocr"],
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
