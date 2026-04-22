import { Trash2 } from "lucide-react";

import type { ConversationRecord } from "@/api/types";
import { cn } from "@/lib/cn";
import { formatConversationTimestamp, formatMessageCount } from "@/lib/formatters";

interface ConversationListItemProps {
  conversation: ConversationRecord;
  isActive: boolean;
  onDelete: () => void;
  onSelect: () => void;
}

export function ConversationListItem({
  conversation,
  isActive,
  onDelete,
  onSelect,
}: ConversationListItemProps): JSX.Element {
  return (
    <article
      className={cn(
        "rounded-[1.4rem] border p-4 transition-colors",
        isActive
          ? "border-sky-400 bg-sky-50 dark:border-sky-600 dark:bg-sky-950/30"
          : "border-slate-200/80 bg-white/75 dark:border-slate-800 dark:bg-slate-950/35",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <button
          type="button"
          onClick={onSelect}
          className="min-w-0 text-left"
        >
          <h3 className="truncate text-sm font-semibold">{conversation.title}</h3>
          <p className="mt-2 text-xs text-slate-500">
            {formatConversationTimestamp(conversation.updatedAt)} •{" "}
            {formatMessageCount(conversation.messageCount)}
          </p>
        </button>
        <button
          type="button"
          onClick={onDelete}
          className="rounded-full p-2 text-slate-500 transition-colors hover:bg-rose-100 hover:text-rose-700 dark:hover:bg-rose-950/40 dark:hover:text-rose-300"
          aria-label={`Delete ${conversation.title}`}
        >
          <Trash2 className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </article>
  );
}
