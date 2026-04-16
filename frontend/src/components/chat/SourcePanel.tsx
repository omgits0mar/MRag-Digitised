import { useEffect, useRef } from "react";

import type { ChatMessage } from "@/api/types";

import { SourceCard } from "./SourceCard";

interface SourcePanelProps {
  activeCitationIndex: number | null;
  message: ChatMessage | null;
}

export function SourcePanel({
  activeCitationIndex,
  message,
}: SourcePanelProps): JSX.Element {
  const cardRefs = useRef<Array<HTMLDivElement | null>>([]);

  useEffect(() => {
    if (activeCitationIndex === null) {
      return;
    }

    cardRefs.current[activeCitationIndex]?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [activeCitationIndex]);

  return (
    <aside className="chat-sources rounded-[1.8rem] border border-slate-200/80 bg-white/75 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950/45">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Sources</p>
          <h3 className="mt-2 text-lg font-semibold">Grounding for the focused answer</h3>
        </div>
      </div>

      {message === null ? (
        <div className="mt-4 rounded-[1.4rem] border border-dashed p-4 text-sm text-slate-500 dark:text-slate-300">
          Focus an assistant answer to inspect its supporting chunks.
        </div>
      ) : message.sources === undefined || message.sources.length === 0 ? (
        <div className="mt-4 rounded-[1.4rem] border border-dashed p-4 text-sm text-slate-500 dark:text-slate-300">
          No sources were used for this response.
        </div>
      ) : (
        <div className="mt-4 grid gap-3">
          {message.sources.map((source, index) => (
            <div
              key={source.chunkId}
              ref={(element) => {
                cardRefs.current[index] = element;
              }}
            >
              <SourceCard
                isHighlighted={activeCitationIndex === index}
                source={source}
              />
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
