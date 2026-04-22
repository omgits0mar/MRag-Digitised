import { AlertTriangle, LoaderCircle, RotateCcw, Square, WifiOff } from "lucide-react";

import type { ChatMessage } from "@/api/types";
import { cn } from "@/lib/cn";

interface InlineAssistantStateProps {
  message: ChatMessage;
  onCancel?: (() => void) | undefined;
  onRetry?: (() => void) | undefined;
}

function getStatusLabel(message: ChatMessage): { label: string; tone: string; Icon: typeof LoaderCircle } {
  switch (message.status) {
    case "thinking":
      return {
        Icon: LoaderCircle,
        label: "Thinking",
        tone: "text-slate-500",
      };
    case "streaming":
      return {
        Icon: LoaderCircle,
        label: "Streaming response",
        tone: "text-sky-700 dark:text-sky-300",
      };
    case "cancelled":
      return {
        Icon: Square,
        label: "Cancelled",
        tone: "text-slate-500",
      };
    case "interrupted":
      return {
        Icon: WifiOff,
        label: "Interrupted",
        tone: "text-amber-700 dark:text-amber-300",
      };
    case "error":
      return {
        Icon: AlertTriangle,
        label: "Error",
        tone: "text-rose-700 dark:text-rose-300",
      };
    case "complete":
    default:
      return {
        Icon: LoaderCircle,
        label: "Complete",
        tone: "text-slate-500",
      };
  }
}

export function InlineAssistantState({
  message,
  onCancel,
  onRetry,
}: InlineAssistantStateProps): JSX.Element | null {
  if (message.role !== "assistant") {
    return null;
  }

  const { Icon, label, tone } = getStatusLabel(message);
  const isBusy = message.status === "thinking" || message.status === "streaming";
  const canRetry = message.status === "error" || message.status === "interrupted";

  if (!isBusy && !canRetry && message.status !== "cancelled") {
    return null;
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
      <span className={cn("inline-flex items-center gap-2 font-medium", tone)}>
        <Icon className={cn("h-4 w-4", isBusy ? "animate-spin" : undefined)} aria-hidden="true" />
        {label}
      </span>
      {message.errorMessage !== undefined ? (
        <span className="text-muted-foreground">{message.errorMessage}</span>
      ) : null}
      {isBusy && onCancel !== undefined ? (
        <button
          type="button"
          onClick={onCancel}
          className="rounded-full border px-3 py-1 font-medium transition-colors hover:bg-slate-950/5 dark:hover:bg-slate-50/10"
        >
          Cancel
        </button>
      ) : null}
      {canRetry && onRetry !== undefined ? (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-full border px-3 py-1 font-medium transition-colors hover:bg-slate-950/5 dark:hover:bg-slate-50/10"
        >
          <span className="inline-flex items-center gap-2">
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
            Retry
          </span>
        </button>
      ) : null}
    </div>
  );
}
