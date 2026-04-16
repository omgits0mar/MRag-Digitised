import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import { useSettingsStore, type ThemePreference } from "@/stores/settingsStore";

const SYSTEM_THEME_QUERY = "(prefers-color-scheme: dark)";

function getSystemPreference(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }

  return window.matchMedia(SYSTEM_THEME_QUERY).matches;
}

function resolveTheme(theme: ThemePreference, prefersDark: boolean): "light" | "dark" {
  if (theme === "system") {
    return prefersDark ? "dark" : "light";
  }

  return theme;
}

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps): JSX.Element {
  const theme = useSettingsStore((state) => state.theme);
  const [prefersDark, setPrefersDark] = useState<boolean>(() => getSystemPreference());

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return undefined;
    }

    const mediaQuery = window.matchMedia(SYSTEM_THEME_QUERY);
    const handleChange = (event: MediaQueryListEvent): void => {
      setPrefersDark(event.matches);
    };

    setPrefersDark(mediaQuery.matches);
    mediaQuery.addEventListener("change", handleChange);

    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, []);

  useEffect(() => {
    const resolvedTheme = resolveTheme(theme, prefersDark);
    const rootElement = document.documentElement;

    rootElement.classList.toggle("dark", resolvedTheme === "dark");
    rootElement.dataset.theme = resolvedTheme;
    rootElement.style.colorScheme = resolvedTheme;
  }, [prefersDark, theme]);

  return <>{children}</>;
}

