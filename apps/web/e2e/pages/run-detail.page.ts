// Page Object for /runs/:runId.

import { expect, type Locator, type Page } from "@playwright/test"

export class RunDetailPage {
  readonly page: Page
  readonly heading: Locator
  readonly statusBadge: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.getByRole("heading", { level: 1 })
    this.statusBadge = page.getByTestId("run-status")
  }

  async goto(runId: string): Promise<void> {
    await this.page.goto(`/runs/${runId}`)
  }

  async expectLoaded(issueId: string): Promise<void> {
    await expect(this.heading).toHaveText(issueId)
  }

  tab(name: "overview" | "spec" | "plan" | "sessions" | "gates" | "pr"): Locator {
    return this.page.getByRole("button", { name: new RegExp(`^${name}$`, "i") })
  }
}
