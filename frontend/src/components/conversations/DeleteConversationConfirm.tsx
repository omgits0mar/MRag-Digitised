interface DeleteConversationConfirmProps {
  conversationTitle: string;
  onCancel: () => void;
  onConfirm: () => void;
}

export function DeleteConversationConfirm({
  conversationTitle,
  onCancel,
  onConfirm,
}: DeleteConversationConfirmProps): JSX.Element {
  return (
    <div className="mt-3 rounded-[1.2rem] border border-rose-200 bg-rose-50 p-3 text-sm dark:border-rose-900/60 dark:bg-rose-950/20">
      <p className="font-medium text-rose-900 dark:text-rose-200">
        Delete “{conversationTitle}”?
      </p>
      <p className="mt-1 text-rose-700 dark:text-rose-300">
        This removes the conversation from the list.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onConfirm}
          className="rounded-full bg-rose-600 px-3 py-1.5 font-medium text-white transition-colors hover:bg-rose-700"
        >
          Delete
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-full border px-3 py-1.5 font-medium transition-colors hover:bg-slate-950/5 dark:hover:bg-slate-50/10"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
