import type { ChangeEvent } from "react";

import { useSettingsStore } from "@/stores/settingsStore";

const THEME_OPTIONS = ["system", "light", "dark"] as const;

function SettingsPage(): JSX.Element {
  const selectedModel = useSettingsStore((state) => state.selectedModel);
  const topK = useSettingsStore((state) => state.topK);
  const scoreThreshold = useSettingsStore((state) => state.scoreThreshold);
  const temperature = useSettingsStore((state) => state.temperature);
  const theme = useSettingsStore((state) => state.theme);
  const setModel = useSettingsStore((state) => state.setModel);
  const setTopK = useSettingsStore((state) => state.setTopK);
  const setScoreThreshold = useSettingsStore((state) => state.setScoreThreshold);
  const setTemperature = useSettingsStore((state) => state.setTemperature);
  const setTheme = useSettingsStore((state) => state.setTheme);
  const resetDefaults = useSettingsStore((state) => state.resetDefaults);

  const handleNumberInput =
    (setter: (value: number) => void) =>
    (event: ChangeEvent<HTMLInputElement>): void => {
      setter(Number(event.currentTarget.value));
    };

  return (
    <section className="bg-card text-card-foreground rounded-[2rem] border p-8 shadow-shell">
      <p className="text-sm uppercase tracking-[0.3em] text-slate-500">Settings</p>
      <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-semibold">Preferences already persist across reloads.</h2>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-300">
            These controls are backed by the shared settings store so the shell can react
            immediately without prop drilling.
          </p>
        </div>
        <button
          type="button"
          onClick={resetDefaults}
          className="bg-muted text-muted-foreground hover:bg-accent/10 rounded-full px-4 py-2 text-sm font-semibold transition-colors"
        >
          Reset defaults
        </button>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <form className="grid gap-5">
          <label className="grid gap-2" htmlFor="settings-selected-model">
            <span className="text-sm font-semibold">Selected model</span>
            <input
              id="settings-selected-model"
              type="text"
              aria-label="Selected model"
              value={selectedModel}
              onChange={(event) => {
                setModel(event.currentTarget.value);
              }}
              className="border-border bg-background rounded-2xl border px-4 py-3"
            />
          </label>

          <label className="grid gap-2" htmlFor="settings-top-k">
            <span className="flex items-center justify-between text-sm font-semibold">
              <span>Top-K retrieval</span>
              <span>{topK}</span>
            </span>
            <input
              id="settings-top-k"
              type="range"
              aria-label="Top-K retrieval"
              min="1"
              max="20"
              step="1"
              value={topK}
              onChange={handleNumberInput(setTopK)}
            />
          </label>

          <label className="grid gap-2" htmlFor="settings-score-threshold">
            <span className="flex items-center justify-between text-sm font-semibold">
              <span>Score threshold</span>
              <span>{scoreThreshold.toFixed(2)}</span>
            </span>
            <input
              id="settings-score-threshold"
              type="range"
              aria-label="Score threshold"
              min="0"
              max="1"
              step="0.05"
              value={scoreThreshold}
              onChange={handleNumberInput(setScoreThreshold)}
            />
          </label>

          <label className="grid gap-2" htmlFor="settings-temperature">
            <span className="flex items-center justify-between text-sm font-semibold">
              <span>Temperature</span>
              <span>{temperature.toFixed(1)}</span>
            </span>
            <input
              id="settings-temperature"
              type="range"
              aria-label="Temperature"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={handleNumberInput(setTemperature)}
            />
          </label>

          <label className="grid gap-2" htmlFor="settings-theme">
            <span className="text-sm font-semibold">Theme</span>
            <select
              id="settings-theme"
              aria-label="Theme"
              value={theme}
              onChange={(event) => {
                setTheme(event.currentTarget.value as (typeof THEME_OPTIONS)[number]);
              }}
              className="border-border bg-background rounded-2xl border px-4 py-3"
            >
              {THEME_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </form>

        <aside className="bg-background/70 rounded-[1.75rem] border p-5">
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Live Summary</p>
          <dl className="mt-5 grid gap-4 text-sm">
            <div className="flex items-center justify-between gap-3">
              <dt className="text-slate-500 dark:text-slate-300">Model</dt>
              <dd className="font-semibold">{selectedModel}</dd>
            </div>
            <div className="flex items-center justify-between gap-3">
              <dt className="text-slate-500 dark:text-slate-300">Top-K</dt>
              <dd className="font-semibold">{topK}</dd>
            </div>
            <div className="flex items-center justify-between gap-3">
              <dt className="text-slate-500 dark:text-slate-300">Threshold</dt>
              <dd className="font-semibold">{scoreThreshold.toFixed(2)}</dd>
            </div>
            <div className="flex items-center justify-between gap-3">
              <dt className="text-slate-500 dark:text-slate-300">Temperature</dt>
              <dd className="font-semibold">{temperature.toFixed(1)}</dd>
            </div>
            <div className="flex items-center justify-between gap-3">
              <dt className="text-slate-500 dark:text-slate-300">Theme</dt>
              <dd className="font-semibold capitalize">{theme}</dd>
            </div>
          </dl>
        </aside>
      </div>
    </section>
  );
}

export default SettingsPage;
