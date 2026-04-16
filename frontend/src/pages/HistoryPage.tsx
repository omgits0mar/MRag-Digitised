import { ConversationList } from "@/components/conversations/ConversationList";
import { MessageList } from "@/components/chat/MessageList";
import { useConversationHistory } from "@/hooks/useConversationHistory";
import { useChatStore } from "@/stores/chatStore";

function HistoryPage(): JSX.Element {
  const history = useConversationHistory();
  const messages = useChatStore((state) => state.messages);
  const focusedAssistantMessageId = useChatStore((state) => state.focusedAssistantMessageId);
  const setFocusedAssistantMessage = useChatStore((state) => state.setFocusedAssistantMessage);

  return (
    <section className="grid gap-4 xl:grid-cols-[18rem_minmax(0,1fr)]">
      <ConversationList
        activeId={history.activeId}
        conversations={history.conversations}
        isLoading={history.isLoading}
        onDelete={history.deleteConversation}
        onNewChat={history.startNewConversation}
        onSelect={history.selectConversation}
        title="Conversation archive"
      />

      <div className="rounded-[2rem] border border-slate-200/80 bg-white/80 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950/45">
        <p className="text-xs uppercase tracking-[0.24em] text-slate-500">History</p>
        <h2 className="mt-2 text-2xl font-semibold">Review saved transcripts</h2>
        <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
          Select a conversation to inspect its transcript before returning to the live chat workspace.
        </p>

        {history.lastError !== null ? (
          <p className="mt-4 rounded-[1.2rem] border border-amber-300 bg-amber-100/70 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200">
            {history.lastError.message}
          </p>
        ) : null}

        <div className="mt-6">
          <MessageList
            focusedAssistantMessageId={focusedAssistantMessageId}
            messages={messages}
            onFocusMessage={(messageId) => {
              const message = messages.find((entry) => entry.id === messageId);
              if (message?.role === "assistant") {
                setFocusedAssistantMessage(messageId);
              }
            }}
          />
        </div>
      </div>
    </section>
  );
}

export default HistoryPage;
