import { ArrowDown } from "lucide-react";

interface JumpToLatestButtonProps {
  onClick: () => void;
}

export function JumpToLatestButton({ onClick }: JumpToLatestButtonProps): JSX.Element {
  return (
    <button
      type="button"
      onClick={onClick}
      className="absolute bottom-28 right-6 z-10 inline-flex items-center gap-2 rounded-full bg-slate-950 px-4 py-2 text-sm font-medium text-white shadow-lg transition-transform hover:-translate-y-0.5 dark:bg-white dark:text-slate-950"
    >
      <ArrowDown className="h-4 w-4" aria-hidden="true" />
      Jump to latest
    </button>
  );
}
