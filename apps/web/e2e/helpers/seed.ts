// Test data seed helpers.
//
// createRun(): hits POST /runs/ with a unique issue_id so tests don't collide.
// publishEvent(): publishes directly to the per-run Redis Pub/Sub channel
//   (`run:{run_id}:events`) so SSE tests don't need a real Celery worker
//   to be processing the run. Mirrors the channel format defined in
//   src/infrastructure/adapters/events/redis_run_event_bus.py:25.

import Redis from "ioredis"

import { apiClient, type RunSummary } from "./api-client"

const REDIS_URL = process.env.E2E_REDIS_URL ?? "redis://localhost:6380/0"

let redis: Redis | null = null

function getRedis(): Redis {
  if (!redis) {
    redis = new Redis(REDIS_URL, { maxRetriesPerRequest: 2 })
  }
  return redis
}

export async function disconnectRedis(): Promise<void> {
  if (redis) {
    redis.disconnect()
    redis = null
  }
}

function uniqueIssueId(prefix = "E2E"): string {
  const ts = Date.now().toString(36)
  const rnd = Math.random().toString(36).slice(2, 6)
  return `${prefix}-${ts}-${rnd}`.toUpperCase()
}

export async function createRun(prefix?: string): Promise<RunSummary> {
  return apiClient.createRun(uniqueIssueId(prefix))
}

export async function deleteRunSafe(runId: string): Promise<void> {
  try {
    await apiClient.deleteRun(runId)
  } catch {
    // best-effort cleanup — tests must not fail in afterEach
  }
}

interface AgentEvent {
  type: string
  [key: string]: unknown
}

export async function publishEvent(runId: string, event: AgentEvent): Promise<void> {
  await getRedis().publish(`run:${runId}:events`, JSON.stringify(event))
}

export async function publishEvents(runId: string, events: AgentEvent[]): Promise<void> {
  for (const e of events) {
    await publishEvent(runId, e)
  }
}

export async function publishStreamDone(runId: string): Promise<void> {
  await publishEvent(runId, { type: "_stream_done" })
}

export const sampleEvents = {
  assistantText(text: string): AgentEvent {
    return {
      type: "assistant",
      message: { content: [{ type: "text", text }] },
    }
  },
  toolUse(name: string): AgentEvent {
    return { type: "tool_use", name }
  },
}
