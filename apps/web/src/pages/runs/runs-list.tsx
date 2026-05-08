// /runs — list + create + dispatch tick.

import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "react-router-dom"

import { api } from "@/api/client"
import type { DispatchResponse, Run } from "@/api/domain"
import { call } from "@/api/fetch-helper"
import {
  Button,
  Card,
  ErrorBanner,
  Input,
  Label,
  Spinner,
  Table,
  Td,
  Th,
} from "@/components/ui"
import { StatusBadge } from "@/components/status-badge"

export const RunsList = () => {
  const qc = useQueryClient()
  const [issueId, setIssueId] = useState("")

  const runsQuery = useQuery({
    queryKey: ["runs", { limit: 50, offset: 0 }],
    queryFn: () =>
      call<Run[]>(
        api.GET("/runs/", {
          params: { query: { limit: 50, offset: 0 } },
        }) as never,
      ),
  })

  const createRun = useMutation({
    mutationFn: (id: string) =>
      call<Run>(
        api.POST("/runs/", { body: { issue_id: id } }) as never,
      ),
    onSuccess: () => {
      setIssueId("")
      qc.invalidateQueries({ queryKey: ["runs"] })
    },
  })

  const dispatchTick = useMutation({
    mutationFn: () => call<DispatchResponse>(api.POST("/runs/dispatch", {}) as never),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["runs"] }),
  })

  const deleteRun = useMutation({
    mutationFn: (id: string) =>
      call<void>(
        api.DELETE("/runs/{run_id}", {
          params: { path: { run_id: id } },
        }) as never,
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["runs"] }),
  })

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between gap-6">
        <div>
          <h1 className="text-xl font-semibold">Runs</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Pipeline executions tracked by Symphony.
          </p>
        </div>
        <Button
          onClick={() => dispatchTick.mutate()}
          disabled={dispatchTick.isPending}
        >
          {dispatchTick.isPending && <Spinner />}
          Dispatch tick
        </Button>
      </header>

      {dispatchTick.data && (
        <Card className="p-3 text-sm">
          <span className="font-mono">outcome:</span>{" "}
          <strong>{dispatchTick.data.outcome}</strong>
          {dispatchTick.data.run_id && (
            <>
              {" · "}
              <span className="font-mono">run_id:</span>{" "}
              {dispatchTick.data.run_id}
            </>
          )}
          {dispatchTick.data.issue_identifier && (
            <>
              {" · "}
              <span className="font-mono">issue:</span>{" "}
              {dispatchTick.data.issue_identifier}
            </>
          )}
        </Card>
      )}
      <ErrorBanner error={dispatchTick.error} />

      <Card className="p-4">
        <Label className="mb-2">Create run from issue</Label>
        <form
          className="flex items-center gap-3"
          onSubmit={(e) => {
            e.preventDefault()
            if (issueId.trim()) createRun.mutate(issueId.trim())
          }}
        >
          <Input
            placeholder="ENG-123"
            value={issueId}
            onChange={(e) => setIssueId(e.target.value)}
            className="max-w-sm font-mono"
          />
          <Button
            type="submit"
            variant="primary"
            disabled={!issueId.trim() || createRun.isPending}
          >
            {createRun.isPending && <Spinner />}
            Create run
          </Button>
        </form>
        <ErrorBanner className="mt-3" error={createRun.error} />
      </Card>

      <ErrorBanner error={runsQuery.error} />
      {runsQuery.isLoading ? (
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <Spinner /> Loading runs…
        </div>
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Issue</Th>
              <Th>Status</Th>
              <Th>Attempt</Th>
              <Th>Created</Th>
              <Th>ID</Th>
              <Th>Actions</Th>
            </tr>
          </thead>
          <tbody>
            {(runsQuery.data ?? []).length === 0 && (
              <tr>
                <Td colSpan={6} className="text-center text-zinc-500">
                  No runs yet.
                </Td>
              </tr>
            )}
            {(runsQuery.data ?? []).map((run) => (
              <tr
                key={run.id}
                data-testid={`run-row-${run.issue_id}`}
                className="hover:bg-zinc-50 dark:hover:bg-zinc-900"
              >
                <Td className="font-mono">
                  <Link
                    to={`/runs/${run.id}`}
                    data-testid={`run-link-${run.issue_id}`}
                    className="font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-zinc-100"
                  >
                    {run.issue_id}
                  </Link>
                </Td>
                <Td>
                  <StatusBadge value={run.status} />
                </Td>
                <Td className="font-mono text-xs">{run.attempt}</Td>
                <Td className="font-mono text-xs">
                  {new Date(run.created_at).toLocaleString()}
                </Td>
                <Td className="font-mono text-xs text-zinc-500">{run.id.slice(0, 8)}</Td>
                <Td>
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/runs/${run.id}/live`}
                      data-testid={`run-live-link-${run.issue_id}`}
                      className="text-xs text-green-600 underline-offset-4 hover:underline dark:text-green-400"
                    >
                      Live
                    </Link>
                    <Button
                      variant="danger"
                      onClick={() => {
                        if (confirm(`Delete run ${run.issue_id}? This cannot be undone.`)) {
                          deleteRun.mutate(run.id)
                        }
                      }}
                    >
                      Delete
                    </Button>
                  </div>
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </div>
  )
}
