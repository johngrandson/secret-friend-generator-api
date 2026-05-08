// Runs list & detail — covers create-via-API → list → detail navigation,
// plus the 404 fallback path.

import { test, expect } from "../fixtures/test-base"
import { RunsListPage } from "../pages/runs-list.page"
import { RunDetailPage } from "../pages/run-detail.page"

test.describe("Runs list and detail", () => {
  test("created run appears in the list", async ({ page, seed }) => {
    const run = await seed.createRun()

    const list = new RunsListPage(page)
    await list.goto()

    // React Query may have loaded the list before the run was created — refresh.
    await page.reload()
    await list.expectRunListed(run.issue_id)
  })

  test("opening a run from the list shows detail page", async ({ page, seed }) => {
    const run = await seed.createRun()

    const list = new RunsListPage(page)
    await list.goto()
    await page.reload()
    await list.openDetail(run.issue_id)

    const detail = new RunDetailPage(page)
    await detail.expectLoaded(run.issue_id)
    await expect(detail.statusBadge).toBeVisible()
  })

  test("unknown run id renders an error or empty state", async ({ page }) => {
    // Send a syntactically valid UUID that doesn't exist.
    await page.goto("/runs/00000000-0000-0000-0000-000000000000")
    // Either the ErrorBanner or the EmptyState is acceptable.
    const errorOrEmpty = page
      .getByText(/not found|error|missing/i)
      .first()
    await expect(errorOrEmpty).toBeVisible({ timeout: 10_000 })
  })
})
