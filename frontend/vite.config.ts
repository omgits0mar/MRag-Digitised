import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { visualizer } from "rollup-plugin-visualizer";
import { defineConfig } from "vite";

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const distDir = path.resolve(rootDir, "dist");
const mockWorkerPath = path.join(distDir, "mockServiceWorker.js");

function removeMockWorkerPlugin() {
  return {
    name: "remove-mock-service-worker",
    closeBundle() {
      if (fs.existsSync(mockWorkerPath)) {
        fs.rmSync(mockWorkerPath, {
          force: true,
        });
      }
    },
  };
}

export default defineConfig(({ mode }) => ({
  plugins: [react(), removeMockWorkerPlugin()],
  resolve: {
    alias: {
      "@": path.resolve(rootDir, "src"),
    },
  },
  build: {
    chunkSizeWarningLimit: 200,
    sourcemap: mode === "analyze",
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          state: ["zustand"],
        },
      },
      plugins:
        mode === "analyze"
          ? [
              visualizer({
                filename: path.join(distDir, "stats.html"),
                gzipSize: true,
                brotliSize: true,
                template: "treemap",
              }),
            ]
          : [],
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./tests/setup.ts",
    css: true,
    include: ["tests/**/*.{ts,tsx}"],
    exclude: ["tests/e2e/**", "tests/setup.ts"],
    coverage: {
      reporter: ["text", "html"],
    },
  },
}));
