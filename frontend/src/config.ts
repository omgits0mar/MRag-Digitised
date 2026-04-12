export interface AppConfig {
  apiBaseUrl: string;
  enableMock: boolean;
  defaultModel: string;
  enableStreaming: boolean;
  apiRequestTimeoutMs: number;
}

export class ConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConfigError";
  }
}

const DEFAULT_TIMEOUT_MS = 30_000;

let cachedConfig: AppConfig | null = null;

function parseBoolean(rawValue: string | undefined, defaultValue: boolean): boolean {
  if (rawValue === undefined || rawValue === "") {
    return defaultValue;
  }

  return rawValue.toLowerCase() === "true";
}

function parseTimeout(rawValue: string | undefined): number {
  if (rawValue === undefined || rawValue === "") {
    return DEFAULT_TIMEOUT_MS;
  }

  const parsedValue = Number(rawValue);
  if (!Number.isFinite(parsedValue) || parsedValue <= 0) {
    throw new ConfigError(
      "Set `VITE_API_REQUEST_TIMEOUT_MS` to a positive integer in `frontend/.env`.",
    );
  }

  return parsedValue;
}

export function loadConfig(env: ImportMetaEnv): AppConfig {
  const apiBaseUrl = env.VITE_API_BASE_URL?.trim();
  if (!apiBaseUrl) {
    throw new ConfigError("Set `VITE_API_BASE_URL` in `frontend/.env`.");
  }

  const defaultModel = env.VITE_DEFAULT_MODEL?.trim();
  if (!defaultModel) {
    throw new ConfigError("Set `VITE_DEFAULT_MODEL` in `frontend/.env`.");
  }

  return {
    apiBaseUrl,
    enableMock: parseBoolean(env.VITE_ENABLE_MOCK, false),
    defaultModel,
    enableStreaming: parseBoolean(env.VITE_ENABLE_STREAMING, false),
    apiRequestTimeoutMs: parseTimeout(env.VITE_API_REQUEST_TIMEOUT_MS),
  };
}

export function getConfig(): AppConfig {
  if (cachedConfig === null) {
    cachedConfig = loadConfig(import.meta.env);
  }

  return cachedConfig;
}

export function resetConfigCache(): void {
  cachedConfig = null;
}

export function setConfigForTests(config: AppConfig | null): void {
  cachedConfig = config;
}
