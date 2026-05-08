// Page Object for /runs/:runId/live — SSE event stream.

import { expect, type Locator, type Page } from "@playwright/test"

export type StreamStatus = "connecting" | "live" | "ended" | "error"

export class RunLivePage {
  readonly page: Page
  readonly heading: Locator
  readonly statusPill: Locator
  readonly waitingMessage: Locator
  readonly reconnectButton: Locator

  constructor(page: Page) {
    this.page = page
    this.heading = page.getByRole("heading", { name: /live stream/i })
    this.statusPill = page.getByTestId("stream-status")
    this.waitingMessage = page.getByTestId("stream-waiting")
    this.reconnectButton = page.getByRole("button", { name: /reconnect/i })
  }

  async goto(runId: string): Promise<void> {
    await this.page.goto(`/runs/${runId}/live`)
  }

  async expectStatus(expected: StreamStatus, timeout = 10_000): Promise<void> {
    await expect(this.statusPill).toHaveAttribute("data-status", expected, { timeout })
  }

  events(): Locator {
    return this.page.getByTestId("stream-event")
  }

  async eventCount(): Promise<number> {
    return await this.events().count()
  }

  async expectEventCount(expected: number, timeout = 10_000): Promise<void> {
    await expect(this.events()).toHaveCount(expected, { timeout })
  }

  async clickReconnect(): Promise<void> {
    await this.reconnectButton.click()
  }
}
