import type { ChatMessage } from "@/api/types";
import { cn } from "@/lib/cn";
import { formatConversationTimestamp } from "@/lib/formatters";
import { MarkdownMessage } from "@/lib/markdown";

import { InlineAssistantState } from "./InlineAssistantState";
import { MessageMeta } from "./MessageMeta";

interface MessageBubbleProps {
  isFocused: boolean;
  message: ChatMessage;
  onCancel?: (() => void) | undefined;
  onCitationActivate?: ((citationIndex: number) => void) | undefined;
  onFocus: () => void;
  onRetry?: (() => void) | undefined;
}

export function MessageBubble({
  isFocused,
  message,
  onCancel,
  onCitationActivate,
  onFocus,
  onRetry,
}: MessageBubbleProps): JSX.Element {
  const isAssistant = message.role === "assistant";
  const showState = message.status !== "complete";

  return (
    <div
      aria-label={`Focus ${message.role} message`}
      role="button"
      tabIndex={0}
      onClick={onFocus}
      onFocus={onFocus}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onFocus();
        }
      }}
      dir="auto"
      className={cn(
        "rounded-[1.8rem] border px-4 py-4 shadow-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-sky-500 sm:px-5",
        isAssistant
          ? "border-slate-200/80 bg-white/85 dark:border-slate-800 dark:bg-slate-950/55"
          : "border-sky-200/80 bg-sky-50/90 dark:border-sky-900 dark:bg-sky-950/40",
        isFocused ? "ring-2 ring-sky-400/70" : undefined,
        isAssistant && message.isFallback ? "border-amber-300 dark:border-amber-700" : undefined,
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
            {message.role}
          </span>
          {isAssistant && message.isFallback ? (
            <span className="rounded-full bg-amber-100 px-2 py-1 text-[11px] font-semibold text-amber-700 dark:bg-amber-950/40 dark:text-amber-300">
              Low confidence
            </span>
          ) : null}
        </div>
        <time className="text-xs text-slate-500">{formatConversationTimestamp(message.createdAt)}</time>
      </div>

      <div className="mt-4">
        {message.content.trim() !== "" ? (
          isAssistant ? (
            <MarkdownMessage
              content={message.content}
              sourceCount={message.sources?.length ?? 0}
              onCitationActivate={onCitationActivate}
            />
          ) : (
            <p className="whitespace-pre-wrap text-sm leading-7 sm:text-[0.95rem]">{message.content}</p>
          )
        ) : message.status === "thinking" ? (
          <p className="text-sm text-slate-500">Waiting for the first token...</p>
        ) : null}
      </div>

      {showState ? (
        <InlineAssistantState message={message} onCancel={onCancel} onRetry={onRetry} />
      ) : null}
      {isAssistant ? <MessageMeta message={message} /> : null}
    </div>
  );
}
