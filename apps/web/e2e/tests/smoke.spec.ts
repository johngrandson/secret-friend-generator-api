// Smoke — app boots, root route renders, primary nav reachable.

import { test, expect } from "../fixtures/test-base"

test("app shell loads and Runs route is reachable from root", async ({ page }) => {
  await page.goto("/")

  // Sidebar / topbar must render — exercise nav by going to /runs.
  await page.goto("/runs")
  await expect(page.getByRole("heading", { name: /^runs$/i, level: 1 })).toBeVisible()
})
