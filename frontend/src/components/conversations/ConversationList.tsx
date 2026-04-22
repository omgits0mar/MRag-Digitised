import { useState } from "react";
import { Plus } from "lucide-react";

import type { ConversationRecord } from "@/api/types";

import { DeleteConversationConfirm } from "./DeleteConversationConfirm";
import { ConversationListItem } from "./ConversationListItem";

interface ConversationListProps {
  activeId: string | null;
  conversations: ConversationRecord[];
  isLoading?: boolean;
  onDelete: (conversationId: string) => Promise<void> | void;
  onNewChat: () => Promise<void> | void;
  onSelect: (conversationId: string) => Promise<void> | void;
  title?: string;
}

export function ConversationList({
  activeId,
  conversations,
  isLoading = false,
  onDelete,
  onNewChat,
  onSelect,
  title = "Conversations",
}: ConversationListProps): JSX.Element {
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  return (
    <section className="rounded-[1.8rem] border border-slate-200/80 bg-white/75 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950/45">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">History</p>
          <h2 className="mt-2 text-lg font-semibold">{title}</h2>
        </div>
        <button
          type="button"
          onClick={() => {
            void onNewChat();
          }}
          className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          New chat
        </button>
      </div>

      <div className="mt-4 grid gap-3">
        {isLoading ? (
          <p className="text-sm text-slate-500">Loading conversations...</p>
        ) : null}
        {!isLoading && conversations.length === 0 ? (
          <p className="rounded-[1.2rem] border border-dashed p-4 text-sm text-slate-500 dark:text-slate-300">
            No saved conversations yet.
          </p>
        ) : null}

        {conversations.map((conversation) => (
          <div key={conversation.id}>
            <ConversationListItem
              conversation={conversation}
              isActive={conversation.id === activeId}
              onDelete={() => {
                setPendingDeleteId(conversation.id);
              }}
              onSelect={() => {
                void onSelect(conversation.id);
              }}
            />
            {pendingDeleteId === conversation.id ? (
              <DeleteConversationConfirm
                conversationTitle={conversation.title}
                onCancel={() => {
                  setPendingDeleteId(null);
                }}
                onConfirm={() => {
                  setPendingDeleteId(null);
                  void onDelete(conversation.id);
                }}
              />
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}
