/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_ENABLE_MOCK?: string;
  readonly VITE_DEFAULT_MODEL?: string;
  readonly VITE_ENABLE_STREAMING?: string;
  readonly VITE_API_REQUEST_TIMEOUT_MS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
