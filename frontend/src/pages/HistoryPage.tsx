import { useEffect } from "react";

import { useConversationStore } from "@/stores/conversationStore";

function HistoryPage(): JSX.Element {
  const conversations = useConversationStore((state) => state.conversations);
  const activeId = useConversationStore((state) => state.activeId);
  const isLoading = useConversationStore((state) => state.isLoading);
  const lastError = useConversationStore((state) => state.lastError);
  const loadConversations = useConversationStore((state) => state.loadConversations);
  const selectConversation = useConversationStore((state) => state.selectConversation);
  const deleteConversation = useConversationStore((state) => state.deleteConversation);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  return (
    <section className="bg-card text-card-foreground rounded-[2rem] border p-8 shadow-shell">
      <p className="text-sm uppercase tracking-[0.3em] text-slate-500">History</p>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-semibold">Conversation history is wired to shared state.</h2>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-300">
            This placeholder route already loads summaries through the central store so later
            features can swap the card list for full history UX without changing routing.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            void loadConversations();
          }}
          className="bg-primary text-primary-foreground hover:opacity-90 rounded-full px-4 py-2 text-sm font-semibold transition-opacity"
        >
          Refresh
        </button>
      </div>

      {lastError !== null ? (
        <p className="mt-6 rounded-2xl border border-amber-300 bg-amber-100/70 px-4 py-3 text-sm text-amber-900">
          {lastError.message}
        </p>
      ) : null}

      <div className="mt-8 grid gap-4">
        {isLoading ? (
          <p className="text-sm text-slate-500 dark:text-slate-300">Loading conversations…</p>
        ) : null}

        {conversations.length === 0 && !isLoading ? (
          <p className="text-sm text-slate-500 dark:text-slate-300">
            No conversations are loaded yet.
          </p>
        ) : null}

        {conversations.map((conversation) => {
          const isActive = conversation.id === activeId;

          return (
            <article
              key={conversation.id}
              className="bg-background/80 rounded-[1.5rem] border p-5 shadow-sm"
            >
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold">{conversation.title}</h3>
                  <p className="mt-2 text-sm text-slate-500 dark:text-slate-300">
                    Updated {new Date(conversation.updated_at).toLocaleString()} •{" "}
                    {conversation.message_count} messages
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      selectConversation(conversation.id);
                    }}
                    className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-accent text-accent-foreground"
                        : "bg-muted text-muted-foreground hover:bg-accent/10"
                    }`}
                  >
                    {isActive ? "Selected" : "Open"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      void deleteConversation(conversation.id);
                    }}
                    className="rounded-full border border-rose-200 px-4 py-2 text-sm font-medium text-rose-700 transition-colors hover:bg-rose-50 dark:border-rose-400/50 dark:text-rose-200 dark:hover:bg-rose-950/30"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default HistoryPage;
