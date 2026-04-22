export interface QuestionRequest {
  question: string;
  conversation_id?: string | null;
  expand?: boolean;
  temperature?: number;
  max_tokens?: number;
}

export interface SourceResponse {
  chunk_id: string;
  doc_id: string;
  text: string;
  relevance_score: number;
  domain_tag?: string | undefined;
  question_type?: string | undefined;
  chunk_index?: number | undefined;
  total_chunks?: number | undefined;
  original_question?: string | undefined;
  original_answer?: string | undefined;
}

export interface TokenUsageResponse {
  prompt_tokens?: number | undefined;
  completion_tokens?: number | undefined;
  total_tokens?: number | undefined;
}

export interface LatencyBreakdownResponse {
  retrieval_ms?: number | undefined;
  search_ms?: number | undefined;
  generation_ms?: number | undefined;
  total_ms?: number | undefined;
  cache_hit?: boolean | undefined;
}

export interface QuestionResponse {
  answer: string;
  confidence_score?: number | undefined;
  is_fallback?: boolean | undefined;
  sources?: SourceResponse[] | undefined;
  response_time_ms?: number | undefined;
  conversation_id?: string | null | undefined;
  token_usage?: TokenUsageResponse | undefined;
  latency?: LatencyBreakdownResponse | undefined;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | "not_ready";
  vector_store: "loaded" | "not_loaded";
  llm_provider: "reachable" | "unreachable";
  database: "connected" | "disconnected";
  uptime_seconds: number;
  persistence_failure_count: number;
}

export interface RegressionFlag {
  metric: string;
  baseline_value: number;
  current_value: number;
  delta_pct: number;
}

export interface EvaluateRequest {
  dataset_path?: string;
  k_values?: number[];
  generate_report?: boolean;
  compare_baseline?: boolean;
}

export interface EvaluateResponse {
  retrieval: Record<string, number>;
  response_quality: Record<string, number>;
  benchmark: Record<string, number>;
  regressions: RegressionFlag[];
  report_path?: string | null;
  total_queries: number;
}

export interface AnalyticsResponse {
  total_queries: number;
  avg_latency_ms: number;
  cache_hit_rate: number;
  top_domains: string[];
  queries_per_day: Record<string, number>;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  completed_at?: string | undefined;
  sources?: SourceResponse[] | undefined;
  token_usage?: TokenUsageResponse | undefined;
  latency?: LatencyBreakdownResponse | undefined;
  confidence_score?: number | undefined;
  is_fallback?: boolean | undefined;
}

export interface ConversationDetail extends ConversationSummary {
  messages: ConversationMessage[];
}

export interface ModelInfo {
  name: string;
  provider: string;
  description: string;
  tier: "fast" | "balanced" | "quality";
}

export interface UploadResponse {
  filename: string;
  extension: string;
  chunks_added: number;
  total_vectors: number;
  ingested_at: number;
}

export interface UploadStatusResponse {
  total_vectors: number;
  allowed_extensions: string[];
  max_bytes: number;
  last_upload: UploadResponse | null;
}

export interface BackendErrorEnvelope {
  error: string;
  detail: string;
  status_code: number;
}

export type ApiError =
  | { kind: "backend_error"; status: number; message: string; detail: string }
  | { kind: "network"; message: string }
  | { kind: "timeout"; message: string }
  | { kind: "cancelled"; message: string }
  | { kind: "not_configured"; message: string };

export type ApiResult<T> =
  | { kind: "ok"; data: T }
  | { kind: "error"; error: ApiError };

export type ChatRole = "user" | "assistant";

export type ChatMessageStatus =
  | "complete"
  | "thinking"
  | "streaming"
  | "cancelled"
  | "interrupted"
  | "error";

export interface RetrievalSource {
  chunkId: string;
  docId: string;
  text: string;
  relevanceScore: number;
  domainTag?: string | undefined;
  questionType?: string | undefined;
  chunkIndex?: number | undefined;
  totalChunks?: number | undefined;
  originalQuestion?: string | undefined;
  originalAnswer?: string | undefined;
}

export interface TokenUsage {
  promptTokens?: number | undefined;
  completionTokens?: number | undefined;
  totalTokens?: number | undefined;
}

export interface LatencyBreakdown {
  retrievalMs?: number | undefined;
  searchMs?: number | undefined;
  generationMs?: number | undefined;
  totalMs?: number | undefined;
  cacheHit?: boolean | undefined;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  conversationId: string | null;
  content: string;
  createdAt: string;
  completedAt?: string | undefined;
  status: ChatMessageStatus;
  sources?: RetrievalSource[] | undefined;
  tokenUsage?: TokenUsage | undefined;
  latency?: LatencyBreakdown | undefined;
  confidenceScore?: number | undefined;
  isFallback?: boolean | undefined;
  errorKind?: ApiError["kind"] | undefined;
  errorMessage?: string | undefined;
}

export interface ConversationRecord {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
  messages?: ChatMessage[] | undefined;
  status?: "idle" | "loading" | "loaded" | "deleting" | undefined;
}

export interface InFlightRequest {
  requestId: string;
  conversationId: string | null;
  userMessageId: string;
  assistantMessageId: string;
  submittedAt: string;
  mode: "stream" | "single";
  firstChunkAt?: string | undefined;
}

export interface StreamStartEvent {
  type: "start";
  request_id?: string | undefined;
  conversation_id?: string | null | undefined;
  created_at?: string | undefined;
}

export interface StreamTokenEvent {
  type: "token";
  content: string;
}

export interface StreamDoneEvent {
  type: "done";
  response: QuestionResponse;
}

export interface StreamErrorEvent {
  type: "error";
  error: BackendErrorEnvelope;
}

export type StreamEvent =
  | StreamStartEvent
  | StreamTokenEvent
  | StreamDoneEvent
  | StreamErrorEvent;

export function normalizeSource(source: SourceResponse): RetrievalSource {
  return {
    chunkId: source.chunk_id,
    docId: source.doc_id,
    text: source.text,
    relevanceScore: source.relevance_score,
    domainTag: source.domain_tag,
    questionType: source.question_type,
    chunkIndex: source.chunk_index,
    totalChunks: source.total_chunks,
    originalQuestion: source.original_question,
    originalAnswer: source.original_answer,
  };
}

export function normalizeTokenUsage(tokenUsage?: TokenUsageResponse): TokenUsage | undefined {
  if (tokenUsage === undefined) {
    return undefined;
  }

  return {
    promptTokens: tokenUsage.prompt_tokens,
    completionTokens: tokenUsage.completion_tokens,
    totalTokens: tokenUsage.total_tokens,
  };
}

export function normalizeLatency(
  latency?: LatencyBreakdownResponse,
  responseTimeMs?: number,
): LatencyBreakdown | undefined {
  if (latency === undefined && responseTimeMs === undefined) {
    return undefined;
  }

  return {
    retrievalMs: latency?.retrieval_ms,
    searchMs: latency?.search_ms,
    generationMs: latency?.generation_ms,
    totalMs: latency?.total_ms ?? responseTimeMs,
    cacheHit: latency?.cache_hit,
  };
}

export function normalizeConversationMessage(
  message: ConversationMessage,
  conversationId: string,
): ChatMessage {
  return {
    id: message.id,
    role: message.role,
    conversationId,
    content: message.content,
    createdAt: message.created_at,
    completedAt: message.completed_at ?? message.created_at,
    status: "complete",
    sources: message.sources?.map(normalizeSource),
    tokenUsage: normalizeTokenUsage(message.token_usage),
    latency: normalizeLatency(message.latency),
    confidenceScore: message.confidence_score,
    isFallback: message.is_fallback,
  };
}

export function normalizeConversationRecord(
  conversation: ConversationSummary | ConversationDetail,
): ConversationRecord {
  return {
    id: conversation.id,
    title: conversation.title,
    createdAt: conversation.created_at,
    updatedAt: conversation.updated_at,
    messageCount: conversation.message_count,
    messages:
      "messages" in conversation
        ? conversation.messages.map((message) =>
            normalizeConversationMessage(message, conversation.id),
          )
        : undefined,
    status: "messages" in conversation ? "loaded" : "idle",
  };
}

export function createAssistantMessageFromResponse(
  response: QuestionResponse,
  options: {
    id: string;
    createdAt: string;
    completedAt?: string;
    conversationId?: string | null;
    content?: string;
    status?: ChatMessageStatus;
  },
): ChatMessage {
  return {
    id: options.id,
    role: "assistant",
    conversationId: response.conversation_id ?? options.conversationId ?? null,
    content: options.content ?? response.answer,
    createdAt: options.createdAt,
    completedAt: options.completedAt ?? new Date().toISOString(),
    status: options.status ?? "complete",
    sources: response.sources?.map(normalizeSource),
    tokenUsage: normalizeTokenUsage(response.token_usage),
    latency: normalizeLatency(response.latency, response.response_time_ms),
    confidenceScore: response.confidence_score,
    isFallback: response.is_fallback,
  };
}

export function getConversationTitle(question: string): string {
  const trimmed = question.trim().replace(/\s+/g, " ");
  if (trimmed.length <= 48) {
    return trimmed;
  }

  return `${trimmed.slice(0, 45)}...`;
}
