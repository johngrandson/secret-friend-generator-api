// Playwright config — E2E tests for the Symphony test harness frontend.
//
// The backend (uvicorn :8765, Celery worker, Postgres :5437, Redis :6380)
// must be running BEFORE the suite starts — `globalSetup` health-checks the
// API and fails fast with an actionable message if it is not up.
//
// Vite (port 5173) is started by Playwright via `webServer` with
// `reuseExistingServer: true`, so running `./dev.sh` first works too.

import { defineConfig, devices } from "@playwright/test"

const FRONTEND_URL = process.env.E2E_FRONTEND_URL ?? "http://localhost:5173"
const BACKEND_URL = process.env.E2E_BACKEND_URL ?? "http://localhost:8765"

export default defineConfig({
  testDir: "./e2e/tests",
  outputDir: "./test-results",
  fullyParallel: false, // Tests share Postgres state — keep serial until isolated.
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  timeout: 30_000,
  expect: { timeout: 5_000 },
  globalSetup: "./e2e/global-setup.ts",
  use: {
    baseURL: FRONTEND_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
    extraHTTPHeaders: {
      // Default approver — pages that require it can override per-test.
      "X-Approver-Id": process.env.E2E_APPROVER_ID ?? "e2e-approver",
    },
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev",
    url: FRONTEND_URL,
    reuseExistingServer: true,
    timeout: 60_000,
    stdout: "ignore",
    stderr: "pipe",
    env: {
      VITE_API_URL: BACKEND_URL,
    },
  },
  metadata: {
    backendUrl: BACKEND_URL,
    frontendUrl: FRONTEND_URL,
  },
})
