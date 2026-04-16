import { useState } from "react";
import { ChevronDown } from "lucide-react";

import type { ChatMessage } from "@/api/types";
import { cn } from "@/lib/cn";
import {
  formatLatency,
  formatTokenCount,
  getTotalLatency,
  getTotalTokens,
  hasMessageMeta,
} from "@/lib/formatters";

interface MessageMetaProps {
  message: ChatMessage;
}

export function MessageMeta({ message }: MessageMetaProps): JSX.Element | null {
  const [isExpanded, setIsExpanded] = useState(false);

  if (message.role !== "assistant" || !hasMessageMeta(message)) {
    return null;
  }

  const totalTokens = getTotalTokens(message.tokenUsage);
  const totalLatency = getTotalLatency(message.latency);

  return (
    <div className="mt-4 rounded-2xl border border-slate-200/70 bg-slate-50/70 p-3 text-xs dark:border-slate-800 dark:bg-slate-950/30">
      <button
        type="button"
        onClick={() => {
          setIsExpanded((current) => !current);
        }}
        className="flex w-full items-center justify-between gap-3 text-left"
      >
        <div className="flex flex-wrap items-center gap-2">
          {totalTokens !== undefined ? (
            <span className="rounded-full bg-white px-2 py-1 font-medium dark:bg-slate-900">
              {formatTokenCount(totalTokens)}
            </span>
          ) : null}
          {totalLatency !== undefined ? (
            <span className="rounded-full bg-white px-2 py-1 font-medium dark:bg-slate-900">
              {formatLatency(totalLatency)}
            </span>
          ) : null}
          {message.latency?.cacheHit ? (
            <span className="rounded-full bg-emerald-100 px-2 py-1 font-medium text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
              Cache hit
            </span>
          ) : null}
        </div>
        <span className="inline-flex items-center gap-2 font-medium text-slate-500">
          Details
          <ChevronDown
            className={cn("h-4 w-4 transition-transform", isExpanded ? "rotate-180" : undefined)}
            aria-hidden="true"
          />
        </span>
      </button>
      {isExpanded ? (
        <dl className="mt-3 grid gap-2 text-sm text-slate-600 dark:text-slate-300">
          {message.tokenUsage?.promptTokens !== undefined ? (
            <div className="flex items-center justify-between gap-3">
              <dt>Prompt tokens</dt>
              <dd>{message.tokenUsage.promptTokens}</dd>
            </div>
          ) : null}
          {message.tokenUsage?.completionTokens !== undefined ? (
            <div className="flex items-center justify-between gap-3">
              <dt>Completion tokens</dt>
              <dd>{message.tokenUsage.completionTokens}</dd>
            </div>
          ) : null}
          {message.latency?.retrievalMs !== undefined ? (
            <div className="flex items-center justify-between gap-3">
              <dt>Retrieval latency</dt>
              <dd>{formatLatency(message.latency.retrievalMs)}</dd>
            </div>
          ) : null}
          {message.latency?.searchMs !== undefined ? (
            <div className="flex items-center justify-between gap-3">
              <dt>Search latency</dt>
              <dd>{formatLatency(message.latency.searchMs)}</dd>
            </div>
          ) : null}
          {message.latency?.generationMs !== undefined ? (
            <div className="flex items-center justify-between gap-3">
              <dt>Generation latency</dt>
              <dd>{formatLatency(message.latency.generationMs)}</dd>
            </div>
          ) : null}
          {totalLatency !== undefined ? (
            <div className="flex items-center justify-between gap-3 font-medium">
              <dt>Total latency</dt>
              <dd>{formatLatency(totalLatency)}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}
    </div>
  );
}
