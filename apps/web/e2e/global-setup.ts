// Global setup — runs once before the entire suite.
//
// Verifies:
//   1. Backend is reachable on E2E_BACKEND_URL (default :8765).
//   2. Redis is reachable on E2E_REDIS_URL (default :6380) — used by
//      seed.publishEvent().
//
// Fails fast with an actionable error message so contributors don't waste
// minutes debugging "test stuck on connecting" symptoms.

import Redis from "ioredis"

const BACKEND_URL = process.env.E2E_BACKEND_URL ?? "http://localhost:8765"
const REDIS_URL = process.env.E2E_REDIS_URL ?? "redis://localhost:6380/0"

async function checkBackend(): Promise<void> {
  // The app exposes /openapi.json unconditionally — cheaper than wiring a
  // dedicated /health endpoint and equally good as a liveness probe.
  const url = `${BACKEND_URL}/openapi.json`
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(5_000) })
    if (!res.ok) {
      throw new Error(`backend at ${BACKEND_URL} responded ${res.status}`)
    }
  } catch (err) {
    const hint = err instanceof Error ? err.message : String(err)
    throw new Error(
      `[e2e] Backend not reachable at ${BACKEND_URL} (${hint}).\n` +
        `Start the API first:\n` +
        `  docker compose -f docker/docker-compose.yml up -d   # postgres + redis\n` +
        `  ./dev.sh                                            # uvicorn + celery + vite\n` +
        `Then re-run the suite from apps/web/.`,
    )
  }
}

async function checkRedis(): Promise<void> {
  const client = new Redis(REDIS_URL, { lazyConnect: true, connectTimeout: 5_000, maxRetriesPerRequest: 1 })
  try {
    await client.connect()
    await client.ping()
  } catch (err) {
    const hint = err instanceof Error ? err.message : String(err)
    throw new Error(
      `[e2e] Redis not reachable at ${REDIS_URL} (${hint}).\n` +
        `Start the dev stack with:\n` +
        `  docker compose -f docker/docker-compose.yml up -d`,
    )
  } finally {
    client.disconnect()
  }
}

export default async function globalSetup(): Promise<void> {
  await checkBackend()
  await checkRedis()
}
