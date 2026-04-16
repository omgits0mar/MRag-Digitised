import { Menu } from "lucide-react";

import { startFreshChatFromShell } from "@/hooks/useChatSession";
import { useChatStore } from "@/stores/chatStore";
import { useConversationStore } from "@/stores/conversationStore";
import { useSettingsStore } from "@/stores/settingsStore";

interface HeaderProps {
  showMenuButton: boolean;
  onMenuToggle: () => void;
  healthLabel?: string;
  menuExpanded?: boolean;
  menuControlsId?: string;
}

export function Header({
  showMenuButton,
  onMenuToggle,
  healthLabel = "Health check pending",
  menuExpanded = false,
  menuControlsId,
}: HeaderProps): JSX.Element {
  const selectedModel = useSettingsStore((state) => state.selectedModel);
  const theme = useSettingsStore((state) => state.theme);
  const activeConversationId = useChatStore((state) => state.activeConversationId);
  const conversations = useConversationStore((state) => state.conversations);
  const themeLabel = `Theme: ${theme}`;
  const activeConversationTitle =
    activeConversationId === null
      ? "New conversation"
      : conversations.find((conversation) => conversation.id === activeConversationId)?.title ??
        "Active conversation";

  return (
    <header className="border-border bg-card/90 text-card-foreground sticky top-0 z-20 border-b backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          {showMenuButton ? (
            <button
              type="button"
              onClick={onMenuToggle}
              className="border-border bg-background/70 hover:bg-muted inline-flex h-11 w-11 items-center justify-center rounded-full border transition-colors"
              aria-label="Open navigation menu"
              aria-expanded={menuExpanded}
              aria-controls={menuControlsId}
            >
              <Menu className="h-5 w-5" aria-hidden="true" />
            </button>
          ) : null}
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-slate-500">Digitised</p>
            <h1 className="text-lg font-semibold sm:text-xl">Multilingual RAG Platform</h1>
            <p className="mt-1 text-xs text-slate-500">{activeConversationTitle}</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => {
              void startFreshChatFromShell();
            }}
            className="rounded-full bg-slate-950 px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
          >
            New chat
          </button>
          <div
            className="bg-muted text-muted-foreground max-w-[15rem] truncate rounded-full px-3 py-2 text-xs font-medium"
            title={selectedModel}
          >
            Model: {selectedModel}
          </div>
          <div className="bg-background/70 text-muted-foreground rounded-full border px-3 py-2 text-xs font-medium">
            {themeLabel}
          </div>
          <div
            className="border-border bg-background/70 rounded-full border px-3 py-2 text-xs font-medium"
            aria-live="polite"
          >
            {healthLabel}
          </div>
        </div>
      </div>
    </header>
  );
}
