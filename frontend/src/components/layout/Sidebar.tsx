import { NavLink } from "react-router-dom";

import { cn } from "@/lib/cn";

interface SidebarProps {
  mobile: boolean;
  open: boolean;
  onNavigate: () => void;
}

const navItems = [
  { to: "/", label: "Chat" },
  { to: "/history", label: "History" },
  { to: "/settings", label: "Settings" },
];

export function Sidebar({
  mobile,
  open,
  onNavigate,
}: SidebarProps): JSX.Element | null {
  if (mobile && !open) {
    return null;
  }

  return (
    <aside
      aria-label="Primary"
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
        </div>
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
  );
}
