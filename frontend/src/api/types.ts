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
}

export interface QuestionResponse {
  answer: string;
  confidence_score: number;
  is_fallback: boolean;
  sources: SourceResponse[];
  response_time_ms: number;
  conversation_id?: string | null;
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
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
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
