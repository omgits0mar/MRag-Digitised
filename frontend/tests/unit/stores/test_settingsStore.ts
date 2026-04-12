import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  createSettingsDefaults,
  rehydrateSettingsStore,
  resetSettingsStore,
  SETTINGS_STORAGE_KEY,
  useSettingsStore,
} from "@/stores/settingsStore";

describe("settingsStore", () => {
  beforeEach(async () => {
    localStorage.clear();
    resetSettingsStore();
    await rehydrateSettingsStore();
    vi.restoreAllMocks();
  });

  it("persists preferences and can rehydrate them from localStorage", async () => {
    useSettingsStore.getState().setModel("gpt-4.1");
    useSettingsStore.getState().setTopK(9);
    useSettingsStore.getState().setTheme("dark");

    const persistedSnapshot = localStorage.getItem(SETTINGS_STORAGE_KEY);

    expect(persistedSnapshot).toContain("gpt-4.1");
    expect(persistedSnapshot).toContain("\"topK\":9");
    expect(persistedSnapshot).toContain("\"theme\":\"dark\"");

    resetSettingsStore();
    localStorage.setItem(SETTINGS_STORAGE_KEY, persistedSnapshot ?? "");
    await rehydrateSettingsStore();

    expect(useSettingsStore.getState()).toMatchObject({
      selectedModel: "gpt-4.1",
      theme: "dark",
      topK: 9,
    });
  });

  it("falls back to defaults when localStorage contains corrupt JSON", async () => {
    localStorage.setItem(SETTINGS_STORAGE_KEY, "{not-json");
    resetSettingsStore();
    await rehydrateSettingsStore();

    expect(useSettingsStore.getState()).toMatchObject(createSettingsDefaults());
  });

  it("falls back to defaults when the stored schema version is unsupported", async () => {
    localStorage.setItem(
      SETTINGS_STORAGE_KEY,
      JSON.stringify({
        state: {
          schemaVersion: 999,
          selectedModel: "old-model",
          theme: "dark",
          topK: 20,
        },
        version: 999,
      }),
    );

    resetSettingsStore();
    await rehydrateSettingsStore();

    expect(useSettingsStore.getState()).toMatchObject(createSettingsDefaults());
  });
});
