import { defineConfig, devices } from "@playwright/test";

/**
 * Browser checks that exercise the UI against a locally started, seeded API.
 *
 * The API is deliberately not started here: the caller must provision a
 * disposable database, run Alembic and seed it first. That keeps this config
 * incapable of targeting a shared or hosted environment by accident.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  testIgnore: "**/governed-action-flows.spec.ts",
  timeout: 60_000,
  fullyParallel: false,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:3101",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8100 npm run dev -- --hostname 127.0.0.1 --port 3101",
    url: "http://127.0.0.1:3101",
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
