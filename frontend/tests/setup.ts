import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, vi } from "vitest";

import { setConfigForTests } from "@/config";
import { handlers } from "@/mocks/handlers";

export const server = setupServer(...handlers);

function createMemoryStorage(): Storage {
  const store = new Map<string, string>();

  return {
    get length() {
      return store.size;
    },
    clear() {
      store.clear();
    },
    getItem(key: string) {
      return store.get(key) ?? null;
    },
    key(index: number) {
      return Array.from(store.keys())[index] ?? null;
    },
    removeItem(key: string) {
      store.delete(key);
    },
    setItem(key: string, value: string) {
      store.set(key, value);
    },
  };
}

if (
  typeof globalThis.localStorage === "undefined" ||
  typeof globalThis.localStorage.getItem !== "function"
) {
  const memoryStorage = createMemoryStorage();

  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: memoryStorage,
  });

  if (typeof window !== "undefined") {
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      value: memoryStorage,
    });
  }
}

if (typeof window !== "undefined") {
  Object.defineProperty(window, "AbortController", {
    configurable: true,
    value: globalThis.AbortController,
  });
  Object.defineProperty(window, "AbortSignal", {
    configurable: true,
    value: globalThis.AbortSignal,
  });
}

if (typeof window !== "undefined" && window.matchMedia === undefined) {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

if (typeof window !== "undefined" && window.scrollTo === undefined) {
  Object.defineProperty(window, "scrollTo", {
    configurable: true,
    value: vi.fn(),
  });
}

if (globalThis.crypto === undefined || globalThis.crypto.randomUUID === undefined) {
  Object.defineProperty(globalThis, "crypto", {
    configurable: true,
    value: {
      randomUUID: () => "00000000-0000-4000-8000-000000000001",
    },
  });
}

beforeAll(() => {
  setConfigForTests({
    apiBaseUrl: "http://localhost:8000",
    apiRequestTimeoutMs: 30_000,
    defaultModel: "llama-3.1-8b-instant",
    enableMock: false,
    enableStreaming: false,
  });

  server.listen({
    onUnhandledRequest: "error",
  });
});

afterEach(() => {
  globalThis.localStorage.clear();
  server.resetHandlers();
  cleanup();
});

afterAll(() => {
  server.close();
});
