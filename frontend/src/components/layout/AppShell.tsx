import { Suspense, useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { useHealthCheck } from "@/hooks/useHealthCheck";

const MOBILE_BREAKPOINT_PX = 768;

function getIsMobile(): boolean {
  return window.innerWidth <= MOBILE_BREAKPOINT_PX;
}

export function AppShell(): JSX.Element {
  const location = useLocation();
  const healthLabel = useHealthCheck();
  const [isMobile, setIsMobile] = useState<boolean>(() => getIsMobile());
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(() => !getIsMobile());

  useEffect(() => {
    const handleResize = (): void => {
      const nextIsMobile = getIsMobile();
      setIsMobile(nextIsMobile);
      setIsSidebarOpen(!nextIsMobile);
    };

    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  useEffect(() => {
    if (isMobile) {
      setIsSidebarOpen(false);
    }
  }, [isMobile, location.pathname]);

  return (
    <div className="min-h-screen bg-transparent text-slate-950 dark:text-slate-50">
      <div className="mx-auto flex min-h-screen max-w-[1600px]">
        <Sidebar
          mobile={isMobile}
          open={isSidebarOpen}
          onNavigate={() => {
            if (isMobile) {
              setIsSidebarOpen(false);
            }
          }}
        />
        <div className="flex min-h-screen min-w-0 flex-1 flex-col">
          <Header
            showMenuButton={isMobile}
            healthLabel={healthLabel}
            onMenuToggle={() => {
              setIsSidebarOpen((current) => !current);
            }}
          />
          <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
            <div className="mx-auto w-full max-w-6xl">
              <Suspense
                fallback={
                  <div className="bg-card text-card-foreground rounded-[2rem] border p-8 shadow-shell">
                    Loading view…
                  </div>
                }
              >
                <Outlet />
              </Suspense>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
