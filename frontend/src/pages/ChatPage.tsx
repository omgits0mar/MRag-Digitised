function ChatPage(): JSX.Element {
  return (
    <section className="bg-card text-card-foreground rounded-[2rem] border p-8 shadow-shell">
      <p className="text-sm uppercase tracking-[0.3em] text-slate-500">Chat</p>
      <h2 className="mt-3 text-3xl font-semibold">Ask multilingual questions with confidence.</h2>
      <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-300">
        This placeholder marks the future chat workspace. Feature 006 will wire the
        question composer, streamed answers, and cited retrieval sources into this route.
      </p>
    </section>
  );
}

export default ChatPage;
