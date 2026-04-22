import { useEffect, useRef } from "react";
import { NavLink } from "react-router-dom";

import { startFreshChatFromShell } from "@/hooks/useChatSession";
import { cn } from "@/lib/cn";
import { useChatStore } from "@/stores/chatStore";
import { useConversationStore } from "@/stores/conversationStore";

interface SidebarProps {
  mobile: boolean;
  open: boolean;
  id?: string;
  onNavigate: () => void;
  onDismiss: () => void;
}

const navItems = [
  { to: "/", label: "Chat" },
  { to: "/history", label: "History" },
  { to: "/upload", label: "Upload" },
  { to: "/settings", label: "Settings" },
];

export function Sidebar({
  mobile,
  open,
  id,
  onNavigate,
  onDismiss,
}: SidebarProps): JSX.Element | null {
  const asideRef = useRef<HTMLElement>(null);
  const isDrawer = mobile && open;
  const activeConversationId = useChatStore((state) => state.activeConversationId);
  const conversations = useConversationStore((state) => state.conversations);
  const activeConversationTitle =
    activeConversationId === null
      ? "No conversation selected"
      : conversations.find((conversation) => conversation.id === activeConversationId)?.title ??
        "Conversation selected";

  useEffect(() => {
    if (!isDrawer) {
      return undefined;
    }

    const firstLink = asideRef.current?.querySelector<HTMLAnchorElement>("nav a");
    firstLink?.focus();

    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        onDismiss();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isDrawer, onDismiss]);

  if (mobile && !open) {
    return null;
  }

  return (
    <>
      {isDrawer ? (
        <button
          type="button"
          aria-label="Close navigation menu"
          onClick={onDismiss}
          className="fixed inset-0 z-30 bg-slate-950/40 backdrop-blur-sm"
        />
      ) : null}
      <aside
        ref={asideRef}
        id={id}
        aria-label="Primary"
        role={isDrawer ? "dialog" : undefined}
        aria-modal={isDrawer ? true : undefined}
        className={cn(
          "border-border bg-card/95 text-card-foreground w-full border-r backdrop-blur md:max-w-none",
          mobile
            ? "fixed inset-y-0 left-0 z-40 max-w-72 shadow-shell"
            : "hidden min-h-screen max-w-72 md:block",
        )}
      >
        <div className="border-border flex items-center justify-between border-b px-5 py-4">
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-slate-500">Workspace</p>
            <h2 className="mt-1 text-lg font-semibold">MRAG Console</h2>
            <p className="mt-2 text-xs text-slate-500">{activeConversationTitle}</p>
          </div>
        </div>
        <div className="px-4 pt-4">
          <button
            type="button"
            onClick={() => {
              void startFreshChatFromShell();
              onNavigate();
            }}
            className="w-full rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
          >
            New chat
          </button>
        </div>
        <nav className="flex flex-col gap-2 p-4" aria-label="Main navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) =>
                cn(
                  "rounded-2xl px-4 py-3 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-slate-700 hover:bg-slate-200/70 dark:text-slate-100 dark:hover:bg-slate-800",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 pb-4">
          <div className="bg-muted text-muted-foreground rounded-3xl p-4 text-sm">
            Foundation shell only. Chat and history workflows arrive in later features.
          </div>
        </div>
      </aside>
    </>
  );
}
