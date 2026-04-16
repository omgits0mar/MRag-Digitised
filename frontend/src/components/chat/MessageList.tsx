import type { ChatMessage } from "@/api/types";

import { MessageBubble } from "./MessageBubble";

interface MessageListProps {
  focusedAssistantMessageId: string | null;
  messages: ChatMessage[];
  onCancelMessage?: (messageId: string) => void;
  onCitationActivate?: (messageId: string, citationIndex: number) => void;
  onFocusMessage: (messageId: string) => void;
  onRetryMessage?: (messageId: string) => void;
}

export function MessageList({
  focusedAssistantMessageId,
  messages,
  onCancelMessage,
  onCitationActivate,
  onFocusMessage,
  onRetryMessage,
}: MessageListProps): JSX.Element {
  if (messages.length === 0) {
    return (
      <div className="rounded-[1.8rem] border border-dashed border-slate-300/80 bg-white/70 px-5 py-10 text-center dark:border-slate-700 dark:bg-slate-950/30">
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500">Welcome</p>
        <h2 className="mt-3 text-2xl font-semibold">Ask multilingual questions with confidence.</h2>
        <p className="mt-4 text-sm leading-7 text-slate-600 dark:text-slate-300">
          Start a conversation to stream an answer, inspect citations, and review latency signals.
        </p>
      </div>
    );
  }

  return (
    <ol className="grid gap-4">
      {messages.map((message) => {
        const messageId = message.id;

        return (
          <li key={messageId}>
            <MessageBubble
              isFocused={focusedAssistantMessageId === messageId}
              message={message}
              onCancel={
                message.role === "assistant" && onCancelMessage !== undefined
                  ? () => {
                      onCancelMessage(messageId);
                    }
                  : undefined
              }
              onCitationActivate={
                message.role === "assistant" && onCitationActivate !== undefined
                  ? (citationIndex) => {
                      onCitationActivate(messageId, citationIndex);
                    }
                  : undefined
              }
              onFocus={() => {
                onFocusMessage(messageId);
              }}
              onRetry={
                message.role === "assistant" && onRetryMessage !== undefined
                  ? () => {
                      onRetryMessage(messageId);
                    }
                  : undefined
              }
            />
          </li>
        );
      })}
    </ol>
  );
}
