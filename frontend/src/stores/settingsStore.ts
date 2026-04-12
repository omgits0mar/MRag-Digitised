import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { getConfig } from "@/config";
import { logger } from "@/lib/logger";

export type ThemePreference = "system" | "light" | "dark";

export interface SettingsStoreState {
  schemaVersion: 1;
  selectedModel: string;
  topK: number;
  scoreThreshold: number;
  temperature: number;
  theme: ThemePreference;
  setModel: (model: string) => void;
  setTopK: (value: number) => void;
  setScoreThreshold: (value: number) => void;
  setTemperature: (value: number) => void;
  setTheme: (theme: ThemePreference) => void;
  resetDefaults: () => void;
}

const TOP_K_LIMITS = {
  min: 1,
  max: 20,
} as const;
const SCORE_THRESHOLD_LIMITS = {
  min: 0,
  max: 1,
} as const;
const TEMPERATURE_LIMITS = {
  min: 0,
  max: 2,
} as const;

export const SETTINGS_SCHEMA_VERSION = 1 as const;
export const SETTINGS_STORAGE_KEY = `mrag:settings:v${SETTINGS_SCHEMA_VERSION}`;

function getFallbackModel(): string {
  try {
    return getConfig().defaultModel;
  } catch {
    return "llama-3.1-8b-instant";
  }
}

export function createSettingsDefaults() {
  return {
    schemaVersion: SETTINGS_SCHEMA_VERSION,
    scoreThreshold: 0.35,
    selectedModel: getFallbackModel(),
    temperature: 0.2,
    theme: "system" as ThemePreference,
    topK: 5,
  };
}

function warnInvalidSetting(key: string, value: unknown, reason: string): void {
  logger.warn("settings.invalid", {
    key,
    reason,
    value,
  });
}

function clampNumber(
  key: string,
  value: number,
  limits: { min: number; max: number },
): number | null {
  if (!Number.isFinite(value)) {
    warnInvalidSetting(key, value, "value must be a finite number");
    return null;
  }

  return Math.min(limits.max, Math.max(limits.min, value));
}

function migratePersistedState(
  persistedState: unknown,
  version: number,
): ReturnType<typeof createSettingsDefaults> {
  if (
    version !== SETTINGS_SCHEMA_VERSION ||
    typeof persistedState !== "object" ||
    persistedState === null
  ) {
    return createSettingsDefaults();
  }

  const defaults = createSettingsDefaults();
  const candidate = persistedState as Record<string, unknown>;

  return {
    ...defaults,
    scoreThreshold:
      typeof candidate.scoreThreshold === "number"
        ? candidate.scoreThreshold
        : defaults.scoreThreshold,
    selectedModel:
      typeof candidate.selectedModel === "string" && candidate.selectedModel.trim() !== ""
        ? candidate.selectedModel
        : defaults.selectedModel,
    temperature:
      typeof candidate.temperature === "number" ? candidate.temperature : defaults.temperature,
    theme:
      candidate.theme === "system" || candidate.theme === "light" || candidate.theme === "dark"
        ? candidate.theme
        : defaults.theme,
    topK: typeof candidate.topK === "number" ? candidate.topK : defaults.topK,
  };
}

export const useSettingsStore = create<SettingsStoreState>()(
  persist(
    (set) => ({
      ...createSettingsDefaults(),
      resetDefaults() {
        set(createSettingsDefaults());
      },
      setModel(model) {
        const trimmedModel = model.trim();

        if (trimmedModel === "") {
          warnInvalidSetting("selectedModel", model, "model cannot be empty");
          return;
        }

        set({
          selectedModel: trimmedModel,
        });
      },
      setScoreThreshold(value) {
        const nextValue = clampNumber("scoreThreshold", value, SCORE_THRESHOLD_LIMITS);
        if (nextValue === null) {
          return;
        }

        set({
          scoreThreshold: Number(nextValue.toFixed(2)),
        });
      },
      setTemperature(value) {
        const nextValue = clampNumber("temperature", value, TEMPERATURE_LIMITS);
        if (nextValue === null) {
          return;
        }

        set({
          temperature: Number(nextValue.toFixed(1)),
        });
      },
      setTheme(theme) {
        if (theme !== "system" && theme !== "light" && theme !== "dark") {
          warnInvalidSetting("theme", theme, "theme must be system, light, or dark");
          return;
        }

        set({
          theme,
        });
      },
      setTopK(value) {
        const nextValue = clampNumber("topK", value, TOP_K_LIMITS);
        if (nextValue === null) {
          return;
        }

        set({
          topK: Math.round(nextValue),
        });
      },
    }),
    {
      name: SETTINGS_STORAGE_KEY,
      onRehydrateStorage: () => (_, error) => {
        if (error instanceof Error) {
          logger.warn("settings.rehydrate.failed", {
            error: error.message,
          });
        } else if (error !== undefined) {
          logger.warn("settings.rehydrate.failed", {
            error: String(error),
          });
        }
      },
      partialize: (state) => ({
        schemaVersion: state.schemaVersion,
        scoreThreshold: state.scoreThreshold,
        selectedModel: state.selectedModel,
        temperature: state.temperature,
        theme: state.theme,
        topK: state.topK,
      }),
      storage: createJSONStorage(() => localStorage),
      version: SETTINGS_SCHEMA_VERSION,
      migrate: migratePersistedState,
    },
  ),
);

export function resetSettingsStore(): void {
  useSettingsStore.setState(createSettingsDefaults());
}

export async function rehydrateSettingsStore(): Promise<void> {
  await useSettingsStore.persist.rehydrate();
}
