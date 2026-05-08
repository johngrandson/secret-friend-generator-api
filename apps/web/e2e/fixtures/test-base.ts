// Extended Playwright `test` with seed helpers attached as fixtures.
//
// Usage:
//   import { test, expect } from "../fixtures/test-base"
//   test("...", async ({ page, seed }) => { const run = await seed.createRun() ... })

import { test as base, expect } from "@playwright/test"

import { apiClient } from "../helpers/api-client"
import {
  createRun,
  deleteRunSafe,
  disconnectRedis,
  publishEvent,
  publishEvents,
  publishStreamDone,
  sampleEvents,
} from "../helpers/seed"

interface SeedAPI {
  createRun: typeof createRun
  publishEvent: typeof publishEvent
  publishEvents: typeof publishEvents
  publishStreamDone: typeof publishStreamDone
  events: typeof sampleEvents
  api: typeof apiClient
}

export const test = base.extend<{ seed: SeedAPI; trackedRunIds: string[] }>({
  trackedRunIds: async ({}, use) => {
    const ids: string[] = []
    await use(ids)
    for (const id of ids) {
      await deleteRunSafe(id)
    }
  },
  seed: async ({ trackedRunIds }, use) => {
    await use({
      api: apiClient,
      events: sampleEvents,
      publishEvent,
      publishEvents,
      publishStreamDone,
      createRun: async (prefix?: string) => {
        const run = await createRun(prefix)
        trackedRunIds.push(run.id)
        return run
      },
    })
  },
})

test.afterAll(async () => {
  await disconnectRedis()
})

export { expect }
