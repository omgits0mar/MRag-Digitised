import { useEffect, useState } from "react";

import type { ChatMessage } from "@/api/types";
import { useTranscriptScroll } from "@/hooks/useTranscriptScroll";
import type { ChatSessionViewModel } from "@/hooks/useChatSession";

import { ChatComposer } from "./ChatComposer";
import { JumpToLatestButton } from "./JumpToLatestButton";
import { MessageList } from "./MessageList";
import { SourcePanel } from "./SourcePanel";

interface ActiveCitation {
  citationIndex: number;
  messageId: string;
}

interface ChatWorkspaceProps {
  session: ChatSessionViewModel;
}

function getFocusedAssistantMessage(messages: ChatMessage[], focusedId: string | null): ChatMessage | null {
  if (focusedId !== null) {
    const focusedMessage = messages.find(
      (message) => message.id === focusedId && message.role === "assistant",
    );
    if (focusedMessage !== undefined) {
      return focusedMessage;
    }
  }

  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    if (message?.role === "assistant") {
      return message;
    }
  }

  return null;
}

export function ChatWorkspace({ session }: ChatWorkspaceProps): JSX.Element {
  const [activeCitation, setActiveCitation] = useState<ActiveCitation | null>(null);

  const lastMessage = session.messages[session.messages.length - 1];
  const activityKey = `${session.messages.length}:${lastMessage?.content.length ?? 0}:${lastMessage?.status ?? "idle"}`;
  const { containerRef, jumpToLatestVisible, scrollToLatest } = useTranscriptScroll(activityKey);

  const focusedAssistantMessage = getFocusedAssistantMessage(
    session.messages,
    session.focusedAssistantMessageId,
  );

  useEffect(() => {
    if (
      activeCitation !== null &&
      focusedAssistantMessage !== null &&
      activeCitation.messageId !== focusedAssistantMessage.id
    ) {
      setActiveCitation(null);
    }
  }, [activeCitation, focusedAssistantMessage]);

  return (
    <section className="chat-workspace grid gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
      <div className="flex min-h-[72vh] flex-col rounded-[2rem] border border-slate-200/80 bg-white/80 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950/45">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200/80 px-2 pb-4 dark:border-slate-800">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Chat</p>
            <h2 className="mt-2 text-2xl font-semibold">Grounded answers in one workspace</h2>
          </div>
          <div className="rounded-full bg-slate-950/5 px-3 py-2 text-xs font-medium text-slate-600 dark:bg-slate-50/10 dark:text-slate-200">
            Model: {session.selectedModel}
          </div>
        </div>

        <div className="relative mt-4 min-h-0 flex-1">
          {jumpToLatestVisible ? <JumpToLatestButton onClick={scrollToLatest} /> : null}
          <div ref={containerRef} className="chat-transcript h-full overflow-y-auto pr-1">
            <MessageList
              focusedAssistantMessageId={session.focusedAssistantMessageId}
              messages={session.messages}
              onCancelMessage={() => {
                session.cancelRequest();
              }}
              onCitationActivate={(messageId, citationIndex) => {
                session.focusAssistantMessage(messageId);
                setActiveCitation({
                  citationIndex,
                  messageId,
                });
              }}
              onFocusMessage={(messageId) => {
                const message = session.messages.find((entry) => entry.id === messageId);
                if (message?.role === "assistant") {
                  session.focusAssistantMessage(messageId);
                  setActiveCitation(null);
                }
              }}
              onRetryMessage={(messageId) => {
                void session.retryMessage(messageId);
              }}
            />
          </div>
        </div>

        <div className="mt-4">
          <ChatComposer
            canSubmit={session.canSubmit}
            isBusy={session.isStreaming}
            onCancel={session.cancelRequest}
            onSubmit={session.submitQuestion}
          />
        </div>
      </div>

      <SourcePanel
        activeCitationIndex={
          activeCitation !== null && activeCitation.messageId === focusedAssistantMessage?.id
            ? activeCitation.citationIndex
            : null
        }
        message={focusedAssistantMessage}
      />
    </section>
  );
}
