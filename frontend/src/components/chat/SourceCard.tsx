import { useState } from "react";

import type { RetrievalSource } from "@/api/types";
import { formatRelevanceScore, truncateText } from "@/lib/formatters";

interface SourceCardProps {
  isHighlighted: boolean;
  source: RetrievalSource;
}

export function SourceCard({ isHighlighted, source }: SourceCardProps): JSX.Element {
  const [isExpanded, setIsExpanded] = useState(false);
  const collapsedText = truncateText(source.text);
  const isExpandable = collapsedText !== source.text;
  const previewText = isExpanded ? source.text : collapsedText;

  return (
    <article
      className={`rounded-[1.4rem] border p-4 transition-colors ${
        isHighlighted
          ? "border-sky-400 bg-sky-50 shadow-sm dark:border-sky-500 dark:bg-sky-950/30"
          : "border-slate-200/80 bg-white/80 dark:border-slate-800 dark:bg-slate-950/40"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{source.docId}</p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            {source.domainTag !== undefined ? (
              <span className="rounded-full bg-slate-950/5 px-2 py-1 dark:bg-slate-50/10">
                {source.domainTag}
              </span>
            ) : null}
            {source.questionType !== undefined ? (
              <span className="rounded-full bg-slate-950/5 px-2 py-1 dark:bg-slate-50/10">
                {source.questionType}
              </span>
            ) : null}
            {source.chunkIndex !== undefined && source.totalChunks !== undefined ? (
              <span className="rounded-full bg-slate-950/5 px-2 py-1 dark:bg-slate-50/10">
                Chunk {source.chunkIndex} of {source.totalChunks}
              </span>
            ) : null}
          </div>
        </div>
        <div className="min-w-[7rem] text-right text-sm">
          <p className="font-semibold">{formatRelevanceScore(source.relevanceScore)}</p>
          <div className="mt-2 h-2 rounded-full bg-slate-200 dark:bg-slate-800">
            <div
              className="h-2 rounded-full bg-sky-500"
              style={{ width: `${Math.max(8, source.relevanceScore * 100)}%` }}
            />
          </div>
        </div>
      </div>
      <p className="mt-4 text-sm leading-7 text-slate-700 dark:text-slate-200">{previewText}</p>
      {isExpandable ? (
        <button
          type="button"
          onClick={() => {
            setIsExpanded((current) => !current);
          }}
          className="mt-4 text-sm font-medium text-sky-700 underline decoration-sky-700/40 underline-offset-4 dark:text-sky-300 dark:decoration-sky-300/40"
        >
          {isExpanded ? "Show less" : "Show more"}
        </button>
      ) : null}
    </article>
  );
}
