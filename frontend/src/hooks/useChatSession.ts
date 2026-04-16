import { useRef } from "react";

import { askQuestion } from "@/api/endpoints";
import { streamAnswer, isStreamingUnsupported } from "@/api/streaming";
import {
  createAssistantMessageFromResponse,
  getConversationTitle,
  type ApiError,
  type ChatMessage,
  type ChatMessageStatus,
  type QuestionRequest,
} from "@/api/types";
import { createRequestHandle } from "@/api/client";
import { getConfig } from "@/config";
import { useConversationHistory } from "@/hooks/useConversationHistory";
import { useSettingsStore } from "@/stores/settingsStore";
import { useChatStore } from "@/stores/chatStore";
import { useConversationStore } from "@/stores/conversationStore";

interface SubmitOptions {
  replaceAssistantMessageId?: string | undefined;
  reuseUserMessageId?: string | undefined;
  conversationId?: string | null | undefined;
}

let resetChatFromShell: (() => Promise<void>) | null = null;

export async function startFreshChatFromShell(): Promise<void> {
  await resetChatFromShell?.();
  useConversationStore.getState().clearActiveConversation();
  useChatStore.getState().startNewConversation();
}

export interface ChatSessionViewModel {
  activeConversationId: string | null;
  cancelRequest: () => void;
  canSubmit: boolean;
  conversations: ReturnType<typeof useConversationHistory>["conversations"];
  deleteConversation: ReturnType<typeof useConversationHistory>["deleteConversation"];
  focusAssistantMessage: (messageId: string | null) => void;
  focusedAssistantMessageId: string | null;
  inFlightRequest: ReturnType<typeof useChatStore.getState>["inFlightRequest"];
  isStreaming: boolean;
  lastConversationError: ReturnType<typeof useConversationHistory>["lastError"];
  messages: ChatMessage[];
  retryMessage: (assistantMessageId: string) => Promise<void>;
  selectedModel: string;
  selectConversation: ReturnType<typeof useConversationHistory>["selectConversation"];
  startNewConversation: ReturnType<typeof useConversationHistory>["startNewConversation"];
  submitQuestion: (question: string, options?: SubmitOptions) => Promise<void>;
}

function getRetryQuestion(messages: ChatMessage[], assistantMessageId: string): string | null {
  const assistantIndex = messages.findIndex((message) => message.id === assistantMessageId);
  if (assistantIndex <= 0) {
    return null;
  }

  const previousMessage = messages[assistantIndex - 1];
  return previousMessage?.role === "user" ? previousMessage.content : null;
}

function getInlineErrorMessage(error: ApiError): string {
  switch (error.kind) {
    case "backend_error":
      return error.detail;
    case "timeout":
      return "The request timed out before the assistant finished responding.";
    case "cancelled":
      return "Response cancelled.";
    case "network":
      return "The connection dropped before the assistant finished responding.";
    case "not_configured":
      return error.message;
    default:
      return "The assistant could not complete this response.";
  }
}

export function useChatSession(): ChatSessionViewModel {
  const messages = useChatStore((state) => state.messages);
  const activeConversationId = useChatStore((state) => state.activeConversationId);
  const focusedAssistantMessageId = useChatStore((state) => state.focusedAssistantMessageId);
  const inFlightRequest = useChatStore((state) => state.inFlightRequest);
  const isStreaming = useChatStore((state) => state.isStreaming);
  const appendMessages = useChatStore((state) => state.appendMessages);
  const updateMessage = useChatStore((state) => state.updateMessage);
  const setFocusedAssistantMessage = useChatStore((state) => state.setFocusedAssistantMessage);
  const beginRequest = useChatStore((state) => state.beginRequest);
  const updateInFlightRequest = useChatStore((state) => state.updateInFlightRequest);
  const finishRequest = useChatStore((state) => state.finishRequest);
  const setError = useChatStore((state) => state.setError);
  const setActiveConversation = useChatStore((state) => state.setActiveConversation);

  const selectedModel = useSettingsStore((state) => state.selectedModel);
  const temperature = useSettingsStore((state) => state.temperature);

  const upsertConversation = useConversationStore((state) => state.upsertConversation);

  const requestHandleRef = useRef<ReturnType<typeof createRequestHandle> | null>(null);
  const requestPromiseRef = useRef<Promise<void> | null>(null);

  async function cancelAndWait(): Promise<void> {
    requestHandleRef.current?.cancel();
    await requestPromiseRef.current;
  }

  resetChatFromShell = cancelAndWait;

  const history = useConversationHistory({
    beforeTranscriptChange: cancelAndWait,
  });

  function syncConversationSnapshot(question: string, conversationId: string, completedAt: string): void {
    const transcript = useChatStore.getState().messages;
    const existingConversation = useConversationStore
      .getState()
      .conversations.find((conversation) => conversation.id === conversationId);

    upsertConversation({
      createdAt: existingConversation?.createdAt ?? transcript[0]?.createdAt ?? completedAt,
      id: conversationId,
      messageCount: transcript.length,
      messages: transcript,
      status: "loaded",
      title: existingConversation?.title ?? getConversationTitle(question),
      updatedAt: completedAt,
    });
  }

  function commitAssistantResponse(
    question: string,
    userMessageId: string,
    assistantMessageId: string,
    response: Parameters<typeof createAssistantMessageFromResponse>[0],
  ): void {
    const completedAt = new Date().toISOString();
    const currentAssistant = useChatStore
      .getState()
      .messages.find((message) => message.id === assistantMessageId);

    const assistantMessage = createAssistantMessageFromResponse(response, {
      completedAt,
      content:
        currentAssistant?.status === "streaming" && currentAssistant.content.trim() !== ""
          ? currentAssistant.content
          : response.answer,
      conversationId: response.conversation_id ?? activeConversationId,
      createdAt: currentAssistant?.createdAt ?? completedAt,
      id: assistantMessageId,
    });

    updateMessage(assistantMessageId, () => assistantMessage);

    const conversationId = assistantMessage.conversationId;
    if (conversationId !== null) {
      updateMessage(userMessageId, (message) => ({
        ...message,
        conversationId,
      }));
      setActiveConversation(conversationId);
      syncConversationSnapshot(question, conversationId, completedAt);
    }

    setFocusedAssistantMessage(assistantMessageId);
  }

  function markAssistantError(messageId: string, error: ApiError): void {
    const completedAt = new Date().toISOString();

    updateMessage(messageId, (message) => {
      const hasPartialContent = message.content.trim() !== "";
      const status: ChatMessageStatus =
        error.kind === "cancelled"
          ? "cancelled"
          : hasPartialContent && error.kind === "network"
            ? "interrupted"
            : "error";

      return {
        ...message,
        completedAt,
        errorKind: status === "error" ? error.kind : undefined,
        errorMessage: getInlineErrorMessage(error),
        status,
      };
    });
  }

  async function submitQuestion(question: string, options: SubmitOptions = {}): Promise<void> {
    const trimmedQuestion = question.trim();
    if (trimmedQuestion === "" || useChatStore.getState().inFlightRequest !== null) {
      return;
    }

    const submittedAt = new Date().toISOString();
    const conversationId = options.conversationId ?? useChatStore.getState().activeConversationId;
    const userMessageId = options.reuseUserMessageId ?? crypto.randomUUID();
    const assistantMessageId = options.replaceAssistantMessageId ?? crypto.randomUUID();

    if (options.replaceAssistantMessageId === undefined) {
      appendMessages([
        {
          content: trimmedQuestion,
          conversationId,
          createdAt: submittedAt,
          id: userMessageId,
          role: "user",
          status: "complete",
        },
        {
          content: "",
          conversationId,
          createdAt: submittedAt,
          id: assistantMessageId,
          role: "assistant",
          status: "thinking",
        },
      ]);
    } else {
      updateMessage(assistantMessageId, (message) => ({
        ...message,
        completedAt: undefined,
        content: "",
        errorKind: undefined,
        errorMessage: undefined,
        status: "thinking",
      }));
    }

    beginRequest({
      assistantMessageId,
      conversationId,
      mode: getConfig().enableStreaming ? "stream" : "single",
      requestId: crypto.randomUUID(),
      submittedAt,
      userMessageId,
    });
    setError(null);
    setFocusedAssistantMessage(assistantMessageId);

    const requestHandle = createRequestHandle();
    requestHandleRef.current = requestHandle;

    const request: QuestionRequest = {
      conversation_id: conversationId,
      expand: true,
      question: trimmedQuestion,
      temperature,
    };

    const run = (async () => {
      let result = getConfig().enableStreaming
        ? await streamAnswer(request, {
            onEvent: (event) => {
              if (event.type === "start" && event.conversation_id !== undefined) {
                updateInFlightRequest({
                  conversationId: event.conversation_id ?? null,
                });
              }

              if (event.type === "token") {
                updateInFlightRequest({
                  firstChunkAt:
                    useChatStore.getState().inFlightRequest?.firstChunkAt ?? new Date().toISOString(),
                });
                updateMessage(assistantMessageId, (message) => ({
                  ...message,
                  content: `${message.content}${event.content}`,
                  status: "streaming",
                }));
              }
            },
            signal: requestHandle.signal,
          })
        : await askQuestion(request, { signal: requestHandle.signal });

      if (result.kind === "error" && isStreamingUnsupported(result.error)) {
        updateMessage(assistantMessageId, (message) => ({
          ...message,
          content: "",
          status: "thinking",
        }));
        result = await askQuestion(request, { signal: requestHandle.signal });
      }

      if (result.kind === "ok") {
        commitAssistantResponse(trimmedQuestion, userMessageId, assistantMessageId, result.data);
        return;
      }

      markAssistantError(assistantMessageId, result.error);
      setError(result.error);
    })().finally(() => {
      finishRequest();
      if (requestHandleRef.current === requestHandle) {
        requestHandleRef.current = null;
      }
      if (requestPromiseRef.current === run) {
        requestPromiseRef.current = null;
      }
    });

    requestPromiseRef.current = run;
    await run;
  }

  async function retryMessage(assistantMessageId: string): Promise<void> {
    const retryQuestion = getRetryQuestion(useChatStore.getState().messages, assistantMessageId);
    if (retryQuestion === null) {
      return;
    }

    const assistantMessage = useChatStore
      .getState()
      .messages.find((message) => message.id === assistantMessageId);
    const userIndex = useChatStore
      .getState()
      .messages.findIndex((message) => message.id === assistantMessageId);
    const userMessageId =
      userIndex > 0 ? useChatStore.getState().messages[userIndex - 1]?.id : undefined;

    await submitQuestion(retryQuestion, {
      conversationId: assistantMessage?.conversationId ?? activeConversationId,
      replaceAssistantMessageId: assistantMessageId,
      reuseUserMessageId: userMessageId,
    });
  }

  function cancelRequest(): void {
    requestHandleRef.current?.cancel();
  }

  return {
    activeConversationId,
    cancelRequest,
    canSubmit: inFlightRequest === null,
    conversations: history.conversations,
    deleteConversation: history.deleteConversation,
    focusAssistantMessage: setFocusedAssistantMessage,
    focusedAssistantMessageId,
    inFlightRequest,
    isStreaming,
    lastConversationError: history.lastError,
    messages,
    retryMessage,
    selectedModel,
    selectConversation: history.selectConversation,
    startNewConversation: history.startNewConversation,
    submitQuestion,
  };
}
