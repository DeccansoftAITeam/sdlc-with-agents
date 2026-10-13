import { defineConfig, devices } from "@playwright/test";
import { API_PORT, BACKEND_DIR as backend, WEB_PORT } from "./e2e/constants";

// E2E smoke: the real API + real Postgres + the Next app. Ports differ from `pnpm dev:web`
// (3000 / 8000) so a running dev server is never tested by mistake. Needs Postgres up and
// migrated (`docker compose up -d db`, `alembic upgrade head`); CI does both in the e2e job.

export default defineConfig({
  testDir: "e2e",
  globalSetup: "./e2e/global-setup.ts",
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: { baseURL: `http://127.0.0.1:${WEB_PORT}`, trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `uv run uvicorn app.main:app --port ${API_PORT}`,
      cwd: backend,
      env: { JWT_EPHEMERAL_KEY: "true" },
      url: `http://127.0.0.1:${API_PORT}/healthz`,
      reuseExistingServer: false,
    },
    {
      // A production build, not `next dev`: what users get, and the dev server blocks its
      // HMR/hydration resources on 127.0.0.1, so pages never become interactive.
      command: `pnpm exec next build && pnpm exec next start --port ${WEB_PORT}`,
      env: { API_URL: `http://127.0.0.1:${API_PORT}` },
      url: `http://127.0.0.1:${WEB_PORT}/login`,
      reuseExistingServer: false,
      timeout: 240_000,
    },
  ],
});
