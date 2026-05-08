// /runs/:runId/live — real-time agent event stream via EventSource (SSE).

import { useEffect, useRef, useState } from "react"
import { useParams } from "react-router-dom"

import { Button, Card, Spinner } from "@/components/ui"

type StreamStatus = "connecting" | "live" | "ended" | "error"

interface AgentEvent {
  type: string
  [key: string]: unknown
}

export const RunLive = () => {
  const { runId } = useParams<{ runId: string }>()
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [status, setStatus] = useState<StreamStatus>("connecting")
  const bottomRef = useRef<HTMLDivElement>(null)
  const sourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!runId) return

    const source = new EventSource(`/api/runs/${runId}/stream`)
    sourceRef.current = source

    source.onopen = () => setStatus("live")

    source.onmessage = (e) => {
      const event: AgentEvent = JSON.parse(e.data)
      setEvents((prev) => [...prev, event])
      if (event.type === "_stream_done") {
        setStatus("ended")
        source.close()
      }
    }

    source.onerror = () => {
      setStatus("error")
      source.close()
    }

    return () => {
      source.close()
    }
  }, [runId])

  // Auto-scroll to bottom on new events
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [events])

  const statusColors: Record<StreamStatus, string> = {
    connecting: "text-zinc-400",
    live: "text-green-500",
    ended: "text-zinc-500",
    error: "text-red-500",
  }

  const statusLabels: Record<StreamStatus, string> = {
    connecting: "Connecting…",
    live: "● Live",
    ended: "● Ended",
    error: "● Connection error",
  }

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Live stream</h1>
          <p className="mt-1 font-mono text-xs text-zinc-500">{runId}</p>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`text-sm font-medium ${statusColors[status]}`}
            data-testid="stream-status"
            data-status={status}
          >
            {status === "connecting" && <Spinner className="mr-1 inline-block" />}
            {statusLabels[status]}
          </span>
          {status === "ended" || status === "error" ? (
            <Button
              onClick={() => {
                setEvents([])
                setStatus("connecting")
                const source = new EventSource(`/api/runs/${runId}/stream`)
                sourceRef.current = source
                source.onopen = () => setStatus("live")
                source.onmessage = (e) => {
                  const event: AgentEvent = JSON.parse(e.data)
                  setEvents((prev) => [...prev, event])
                  if (event.type === "_stream_done") {
                    setStatus("ended")
                    source.close()
                  }
                }
                source.onerror = () => {
                  setStatus("error")
                  source.close()
                }
              }}
            >
              Reconnect
            </Button>
          ) : null}
        </div>
      </header>

      <Card className="h-[70vh] overflow-y-auto p-4 font-mono text-xs">
        {events.length === 0 && status === "connecting" && (
          <div
            className="flex h-full items-center justify-center text-zinc-400"
            data-testid="stream-waiting"
          >
            Waiting for events…
          </div>
        )}
        {events.map((event, i) => (
          <div
            key={i}
            data-testid="stream-event"
            data-event-type={event.type}
            className={`mb-1 leading-relaxed ${
              event.type === "_stream_done"
                ? "text-zinc-400"
                : event.type === "assistant"
                  ? "text-zinc-100"
                  : "text-zinc-400"
            }`}
          >
            <span className="mr-2 text-zinc-500">[{event.type}]</span>
            {event.type === "assistant"
              ? renderAssistantEvent(event)
              : JSON.stringify(event, null, 0)}
          </div>
        ))}
        <div ref={bottomRef} />
      </Card>
    </div>
  )
}

function renderAssistantEvent(event: AgentEvent): string {
  const message = event.message as { content?: Array<{ type: string; text?: string }> }
  if (!message?.content) return JSON.stringify(event)
  return message.content
    .filter((c) => c.type === "text")
    .map((c) => c.text ?? "")
    .join("")
}
