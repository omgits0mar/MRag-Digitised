import { useState, type KeyboardEvent } from "react";
import { SendHorizontal, Square } from "lucide-react";

interface ChatComposerProps {
  canSubmit: boolean;
  isBusy: boolean;
  onCancel: () => void;
  onSubmit: (question: string) => Promise<void> | void;
}

export function ChatComposer({
  canSubmit,
  isBusy,
  onCancel,
  onSubmit,
}: ChatComposerProps): JSX.Element {
  const [value, setValue] = useState("");
  const trimmedValue = value.trim();

  async function submit(): Promise<void> {
    if (!canSubmit || trimmedValue === "") {
      return;
    }

    await onSubmit(value);
    setValue("");
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>): void {
    if (event.key !== "Enter" || event.shiftKey) {
      return;
    }

    event.preventDefault();
    void submit();
  }

  return (
    <div className="rounded-[1.8rem] border border-slate-200/80 bg-white/85 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950/50">
      <label className="sr-only" htmlFor="chat-composer-input">
        Ask a question
      </label>
      <textarea
        id="chat-composer-input"
        value={value}
        onChange={(event) => {
          setValue(event.currentTarget.value);
        }}
        onKeyDown={handleKeyDown}
        rows={3}
        placeholder="Ask a multilingual retrieval question..."
        className="min-h-[7rem] w-full resize-none rounded-[1.4rem] border border-transparent bg-slate-100/80 px-4 py-3 text-sm outline-none transition-colors placeholder:text-slate-400 focus:border-sky-400 dark:bg-slate-900/80"
      />
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-500">Enter to send. Shift+Enter for a newline.</p>
        <div className="flex items-center gap-2">
          {isBusy ? (
            <button
              type="button"
              onClick={onCancel}
              className="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-colors hover:bg-slate-950/5 dark:hover:bg-slate-50/10"
            >
              <Square className="h-4 w-4" aria-hidden="true" />
              Cancel
            </button>
          ) : null}
          <button
            type="button"
            disabled={!canSubmit || trimmedValue === ""}
            onClick={() => {
              void submit();
            }}
            className="inline-flex items-center gap-2 rounded-full bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500 dark:disabled:bg-slate-700"
          >
            <SendHorizontal className="h-4 w-4" aria-hidden="true" />
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
