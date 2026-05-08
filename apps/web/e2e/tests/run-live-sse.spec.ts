// Live SSE stream — drives the page via direct Redis publishes so we don't
// depend on a Celery worker actually processing the run during the test.
//
// Channel: `run:{run_id}:events`
// Frontend page: src/pages/runs/run-live.tsx

import { test, expect } from "../fixtures/test-base"
import { RunLivePage } from "../pages/run-live.page"
import { sleep } from "../helpers/wait"

test.describe("Run live stream (SSE)", () => {
  test("golden path: connects, receives events, closes on _stream_done", async ({
    page,
    seed,
  }) => {
    const run = await seed.createRun()
    const live = new RunLivePage(page)

    await live.goto(run.id)
    // Subscriber is attached on page mount; wait for the SSE connection.
    await live.expectStatus("live")

    await seed.publishEvents(run.id, [
      seed.events.assistantText("first event"),
      seed.events.toolUse("Read"),
    ])

    await live.expectEventCount(2)
    await expect(live.events().nth(0)).toContainText("first event")

    await seed.publishStreamDone(run.id)
    await live.expectStatus("ended")
    // The done sentinel is also rendered as a row.
    await live.expectEventCount(3)
  })

  test("reconnect button appears on ended and re-opens the stream", async ({
    page,
    seed,
  }) => {
    const run = await seed.createRun()
    const live = new RunLivePage(page)

    await live.goto(run.id)
    await live.expectStatus("live")

    await seed.publishStreamDone(run.id)
    await live.expectStatus("ended")
    await expect(live.reconnectButton).toBeVisible()

    await live.clickReconnect()
    await live.expectStatus("live")
    await live.expectEventCount(0)

    // Confirm a fresh subscriber receives new events after reconnect.
    await seed.publishEvent(run.id, seed.events.assistantText("after reconnect"))
    await live.expectEventCount(1)
    await expect(live.events().nth(0)).toContainText("after reconnect")
  })

  test("auto-scroll keeps the latest event in view", async ({ page, seed }) => {
    const run = await seed.createRun()
    const live = new RunLivePage(page)

    await live.goto(run.id)
    await live.expectStatus("live")

    const messages = Array.from({ length: 20 }, (_, i) =>
      seed.events.assistantText(`line ${i.toString().padStart(2, "0")}`),
    )
    await seed.publishEvents(run.id, messages)
    await live.expectEventCount(20)

    // Last event must be in the viewport (auto-scrolled).
    const last = live.events().nth(19)
    await expect(last).toBeInViewport()
  })

  test("backpressure: 100 events render in <5s", async ({ page, seed }) => {
    const run = await seed.createRun()
    const live = new RunLivePage(page)

    await live.goto(run.id)
    await live.expectStatus("live")

    const start = Date.now()
    const batch = Array.from({ length: 100 }, (_, i) =>
      seed.events.toolUse(`tool-${i}`),
    )
    await seed.publishEvents(run.id, batch)

    // Yield once to allow buffered SSE frames to flush.
    await sleep(50)
    await live.expectEventCount(100, 5_000)
    const elapsed = Date.now() - start

    expect(elapsed).toBeLessThan(5_000)
  })
})
