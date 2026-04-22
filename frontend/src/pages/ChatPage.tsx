import { ChatWorkspace } from "@/components/chat/ChatWorkspace";
import { ConversationList } from "@/components/conversations/ConversationList";
import { useChatSession } from "@/hooks/useChatSession";

function ChatPage(): JSX.Element {
  const session = useChatSession();

  return (
    <section className="grid gap-4 xl:grid-cols-[18rem_minmax(0,1fr)]">
      <ConversationList
        activeId={session.activeConversationId}
        conversations={session.conversations}
        onDelete={session.deleteConversation}
        onNewChat={session.startNewConversation}
        onSelect={session.selectConversation}
        title="Recent conversations"
      />
      <ChatWorkspace session={session} />
    </section>
  );
}

export default ChatPage;
