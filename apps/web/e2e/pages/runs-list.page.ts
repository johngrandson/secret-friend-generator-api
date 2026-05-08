// Page Object for /runs — list + create + dispatch tick.

import { expect, type Locator, type Page } from "@playwright/test"

export class RunsListPage {
  readonly page: Page
  readonly heading: Locator
  readonly createIssueInput: Locator
  readonly createSubmitButton: Locator
  readonly emptyMessage: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.getByRole("heading", { name: /^runs$/i, level: 1 })
    this.createIssueInput = page.getByPlaceholder("ENG-123")
    this.createSubmitButton = page.getByRole("button", { name: /create run/i })
    this.emptyMessage = page.getByText(/no runs yet/i)
  }

  async goto(): Promise<void> {
    await this.page.goto("/runs")
    await expect(this.heading).toBeVisible()
  }

  rowByIssueId(issueId: string): Locator {
    return this.page.getByTestId(`run-row-${issueId}`)
  }

  async expectRunListed(issueId: string): Promise<void> {
    await expect(this.rowByIssueId(issueId)).toBeVisible()
  }

  async openDetail(issueId: string): Promise<void> {
    await this.page.getByTestId(`run-link-${issueId}`).click()
  }

  async openLive(issueId: string): Promise<void> {
    await this.page.getByTestId(`run-live-link-${issueId}`).click()
  }
}
