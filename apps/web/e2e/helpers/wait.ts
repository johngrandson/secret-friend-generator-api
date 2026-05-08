// Async wait helpers for tests that race against SSE events.

export async function sleep(ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Poll `predicate` every `intervalMs` until it returns true or `timeoutMs`
 * elapses. Throws with `message` on timeout.
 */
export async function waitFor(
  predicate: () => Promise<boolean> | boolean,
  {
    timeoutMs = 5_000,
    intervalMs = 100,
    message = "condition not met in time",
  }: { timeoutMs?: number; intervalMs?: number; message?: string } = {},
): Promise<void> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (await predicate()) return
    await sleep(intervalMs)
  }
  throw new Error(`waitFor timeout (${timeoutMs}ms): ${message}`)
}
