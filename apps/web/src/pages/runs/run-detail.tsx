// /runs/:runId — run detail with tabs (overview/spec/plan/sessions/gates/PR),
// orchestrate trigger, and inline approve/reject for the latest spec & plan.

import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link, useNavigate, useParams } from "react-router-dom"

import { api } from "@/api/client"
import type {
  Artifact,
  OrchestrateResponse,
  RunDetail as RunDetailDTO,
} from "@/api/domain"
import type { Run } from "@/api/domain"
import { call } from "@/api/fetch-helper"
import { ArtifactStatusBadge, StatusBadge } from "@/components/status-badge"
import { MarkdownViewer } from "@/components/markdown-viewer"
import {
  Button,
  Card,
  cn,
  EmptyState,
  ErrorBanner,
  Input,
  Label,
  Spinner,
  Table,
  Td,
  Th,
} from "@/components/ui"
import { useSettingsStore } from "@/stores/settings"

const TERMINAL_STATUSES = new Set(["done", "failed", "cancelled"])

type Tab = "overview" | "spec" | "plan" | "sessions" | "gates" | "pr"
const TABS: ReadonlyArray<{ id: Tab; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "spec", label: "Spec" },
  { id: "plan", label: "Plan" },
  { id: "sessions", label: "Sessions" },
  { id: "gates", label: "Gates" },
  { id: "pr", label: "Pull Request" },
]

export const RunDetail = () => {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const [tab, setTab] = useState<Tab>("overview")
  const [cancelReason, setCancelReason] = useState("")
  const qc = useQueryClient()

  const detail = useQuery({
    queryKey: ["run-detail", runId],
    enabled: Boolean(runId),
    queryFn: () =>
      call<RunDetailDTO>(
        api.GET("/runs/{run_id}/detail", {
          params: { path: { run_id: runId! } },
        }) as never,
      ),
  })

  const orchestrate = useMutation({
    mutationFn: () =>
      call<OrchestrateResponse>(
        api.POST("/runs/{run_id}/orchestrate", {
          params: { path: { run_id: runId! } },
        }) as never,
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["run-detail", runId] }),
  })

  const cancelRun = useMutation({
    mutationFn: (reason: string) =>
      call<Run>(
        api.POST("/runs/{run_id}/cancel", {
          params: { path: { run_id: runId! } },
          body: { reason },
        }) as never,
      ),
    onSuccess: () => {
      setCancelReason("")
      qc.invalidateQueries({ queryKey: ["run-detail", runId] })
      qc.invalidateQueries({ queryKey: ["runs"] })
    },
  })

  const deleteRun = useMutation({
    mutationFn: () =>
      call<void>(
        api.DELETE("/runs/{run_id}", {
          params: { path: { run_id: runId! } },
        }) as never,
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["runs"] })
      navigate("/runs")
    },
  })

  if (!runId) return <p className="text-sm text-zinc-500">Missing run id.</p>
  if (detail.isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-zinc-500">
        <Spinner /> Loading…
      </div>
    )
  }
  if (detail.error) return <ErrorBanner error={detail.error} />
  if (!detail.data) return <EmptyState title="Run not found" />

  const data = detail.data
  const isTerminal = TERMINAL_STATUSES.has(data.run.status)

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3 border-b border-zinc-200 pb-4 dark:border-zinc-800">
        <div className="space-y-1">
          <Link
            to="/runs"
            className="text-xs text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
          >
            ← back to runs
          </Link>
          <h1 className="font-mono text-lg font-semibold">{data.run.issue_id}</h1>
          <div
            className="flex items-center gap-3 text-xs text-zinc-500"
            data-testid="run-status"
            data-status={data.run.status}
          >
            <StatusBadge value={data.run.status} />
            <span>attempt {data.run.attempt}</span>
            <span className="font-mono">{data.run.id}</span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {!isTerminal && (
            <Button
              variant="primary"
              onClick={() => orchestrate.mutate()}
              disabled={orchestrate.isPending}
            >
              {orchestrate.isPending && <Spinner />}
              Orchestrate tick
            </Button>
          )}
          <Button
            variant="danger"
            onClick={() => {
              if (confirm(`Delete run ${data.run.issue_id}? This cannot be undone.`)) {
                deleteRun.mutate()
              }
            }}
            disabled={deleteRun.isPending}
          >
            {deleteRun.isPending && <Spinner />}
            Delete
          </Button>
        </div>
      </header>

      {!isTerminal && (
        <Card className="space-y-3 p-3">
          <Label>Cancel run (mark as CANCELLED with a reason)</Label>
          <div className="flex flex-wrap items-center gap-2">
            <Input
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="e.g. operator decision, blocked, duplicate work"
              className="max-w-md"
            />
            <Button
              variant="secondary"
              onClick={() => cancelRun.mutate(cancelReason.trim())}
              disabled={!cancelReason.trim() || cancelRun.isPending}
            >
              {cancelRun.isPending && <Spinner />}
              Cancel run
            </Button>
          </div>
          <ErrorBanner error={cancelRun.error ?? deleteRun.error} />
        </Card>
      )}

      {orchestrate.data && (
        <Card className="p-3 text-sm">
          <span className="font-mono">outcome:</span>{" "}
          <strong>{orchestrate.data.outcome}</strong>
          {orchestrate.data.paused_reason && (
            <>
              {" · "}
              <span className="font-mono">paused_reason:</span>{" "}
              {orchestrate.data.paused_reason}
            </>
          )}
          {orchestrate.data.final_status && (
            <>
              {" · "}
              <span className="font-mono">final_status:</span>{" "}
              {orchestrate.data.final_status}
            </>
          )}
          {orchestrate.data.error_message && (
            <p className="mt-1 text-red-600 dark:text-red-400">
              {orchestrate.data.error_message}
            </p>
          )}
        </Card>
      )}
      <ErrorBanner error={orchestrate.error} />

      <nav className="flex gap-1 border-b border-zinc-200 dark:border-zinc-800">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "border-b-2 px-3 py-2 text-sm transition-colors",
              tab === t.id
                ? "border-zinc-900 text-zinc-900 dark:border-zinc-100 dark:text-zinc-100"
                : "border-transparent text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100",
            )}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "overview" && <OverviewTab data={data} />}
      {tab === "spec" && (
        <ArtifactTab
          kind="spec"
          artifact={data.latest_spec}
          onMutate={() => qc.invalidateQueries({ queryKey: ["run-detail", runId] })}
        />
      )}
      {tab === "plan" && (
        <ArtifactTab
          kind="plan"
          artifact={data.latest_plan}
          onMutate={() => qc.invalidateQueries({ queryKey: ["run-detail", runId] })}
        />
      )}
      {tab === "sessions" && <SessionsTab data={data} />}
      {tab === "gates" && <GatesTab data={data} />}
      {tab === "pr" && <PullRequestTab data={data} />}
    </div>
  )
}

const OverviewTab: React.FC<{ data: RunDetailDTO }> = ({ data }) => (
  <Card className="p-4">
    <dl className="grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
      <Field label="Workspace" value={data.run.workspace_path ?? "—"} mono />
      <Field
        label="Created"
        value={new Date(data.run.created_at).toLocaleString()}
      />
      <Field
        label="Next attempt"
        value={
          data.run.next_attempt_at
            ? new Date(data.run.next_attempt_at).toLocaleString()
            : "—"
        }
      />
      <Field label="Error" value={data.run.error ?? "—"} />
      <Field
        label="Latest spec"
        value={
          data.latest_spec
            ? `v${data.latest_spec.version} · ${data.latest_spec.approved_at ? "APPROVED" : data.latest_spec.rejection_reason ? "REJECTED" : "PENDING"}`
            : "—"
        }
      />
      <Field
        label="Latest plan"
        value={
          data.latest_plan
            ? `v${data.latest_plan.version} · ${data.latest_plan.approved_at ? "APPROVED" : data.latest_plan.rejection_reason ? "REJECTED" : "PENDING"}`
            : "—"
        }
      />
    </dl>
  </Card>
)

const Field: React.FC<{ label: string; value: string; mono?: boolean }> = ({
  label,
  value,
  mono,
}) => (
  <div>
    <dt className="text-xs uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
      {label}
    </dt>
    <dd className={cn("mt-0.5 break-all", mono && "font-mono text-xs")}>{value}</dd>
  </div>
)

const ArtifactTab: React.FC<{
  kind: "spec" | "plan"
  artifact: Artifact | null
  onMutate: () => void
}> = ({ kind, artifact, onMutate }) => {
  const approverId = useSettingsStore((s) => s.approverId).trim()
  const [rejectReason, setRejectReason] = useState("")

  const approve = useMutation({
    mutationFn: () => {
      if (!artifact) throw new Error("no artifact")
      return call<Artifact>(
        kind === "spec"
          ? (api.POST("/specs/{spec_id}/approve", {
              params: { path: { spec_id: artifact.id } },
            }) as never)
          : (api.POST("/plans/{plan_id}/approve", {
              params: { path: { plan_id: artifact.id } },
            }) as never),
      )
    },
    onSuccess: onMutate,
  })

  const reject = useMutation({
    mutationFn: (reason: string) => {
      if (!artifact) throw new Error("no artifact")
      return call<Artifact>(
        kind === "spec"
          ? (api.POST("/specs/{spec_id}/reject", {
              params: { path: { spec_id: artifact.id } },
              body: { reason },
            }) as never)
          : (api.POST("/plans/{plan_id}/reject", {
              params: { path: { plan_id: artifact.id } },
              body: { reason },
            }) as never),
      )
    },
    onSuccess: () => {
      setRejectReason("")
      onMutate()
    },
  })

  if (!artifact) {
    return <EmptyState title={`No ${kind} yet`} description="Run orchestrate to generate one." />
  }

  const isPending = !artifact.approved_at && !artifact.rejection_reason

  return (
    <div className="space-y-4">
      <Card className="flex flex-wrap items-center justify-between gap-3 p-3">
        <div className="flex items-center gap-3 text-sm">
          <ArtifactStatusBadge
            approvedAt={artifact.approved_at}
            rejectionReason={artifact.rejection_reason}
          />
          <span className="font-mono text-xs text-zinc-500">
            v{artifact.version} · {new Date(artifact.created_at).toLocaleString()}
          </span>
          {artifact.approved_at && artifact.approved_by && (
            <span className="text-xs text-zinc-500">
              by <span className="font-mono">{artifact.approved_by}</span>
            </span>
          )}
        </div>
        {isPending && (
          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              onClick={() => approve.mutate()}
              disabled={!approverId || approve.isPending}
              title={!approverId ? "Set X-Approver-Id in the topbar" : undefined}
            >
              {approve.isPending && <Spinner />}
              Approve
            </Button>
            <Input
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="rejection reason"
              className="w-56"
            />
            <Button
              variant="danger"
              onClick={() => reject.mutate(rejectReason)}
              disabled={!rejectReason.trim() || reject.isPending}
            >
              {reject.isPending && <Spinner />}
              Reject
            </Button>
          </div>
        )}
      </Card>
      <ErrorBanner error={approve.error ?? reject.error} />
      {artifact.rejection_reason && (
        <Card className="border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
          rejected: {artifact.rejection_reason}
        </Card>
      )}
      <Card className="p-4">
        <MarkdownViewer source={artifact.content} empty={`Empty ${kind}.`} />
      </Card>
    </div>
  )
}

const SessionsTab: React.FC<{ data: RunDetailDTO }> = ({ data }) => {
  if (data.agent_sessions.length === 0) {
    return (
      <EmptyState
        title="No agent sessions"
        description="Sessions appear once execution starts. Repository wiring is deferred to F09 — sessions list may be empty even after runs complete."
      />
    )
  }
  return (
    <Table>
      <thead>
        <tr>
          <Th>ID</Th>
          <Th>Model</Th>
          <Th>Tokens</Th>
          <Th>Started</Th>
          <Th>Ended</Th>
        </tr>
      </thead>
      <tbody>
        {data.agent_sessions.map((s) => (
          <tr key={s.id}>
            <Td className="font-mono text-xs">{s.id.slice(0, 8)}</Td>
            <Td className="font-mono text-xs">{s.model ?? "—"}</Td>
            <Td className="font-mono text-xs">{s.total_tokens?.toLocaleString() ?? "—"}</Td>
            <Td className="font-mono text-xs">
              {new Date(s.started_at).toLocaleString()}
            </Td>
            <Td className="font-mono text-xs">
              {s.completed_at ? new Date(s.completed_at).toLocaleString() : "—"}
            </Td>
          </tr>
        ))}
      </tbody>
    </Table>
  )
}

const GatesTab: React.FC<{ data: RunDetailDTO }> = ({ data }) => {
  if (data.gate_results.length === 0) {
    return (
      <EmptyState
        title="No gate results yet"
        description="Gates run after the agent finishes editing. Repository wiring deferred to F09."
      />
    )
  }
  return (
    <Table>
      <thead>
        <tr>
          <Th>Gate</Th>
          <Th>Passed</Th>
          <Th>Recorded</Th>
        </tr>
      </thead>
      <tbody>
        {data.gate_results.map((g) => (
          <tr key={g.id}>
            <Td>{g.gate_name}</Td>
            <Td>{g.status === "passed" ? "✓" : "✗"}</Td>
            <Td className="font-mono text-xs">
              {new Date(g.created_at).toLocaleString()}
            </Td>
          </tr>
        ))}
      </tbody>
    </Table>
  )
}

const PullRequestTab: React.FC<{ data: RunDetailDTO }> = ({ data }) => {
  if (!data.pull_request) {
    return (
      <EmptyState
        title="No pull request yet"
        description="The PR is created after gates pass. Repository wiring deferred to F09."
      />
    )
  }
  const pr = data.pull_request
  return (
    <Card className="p-4">
      <a
        href={pr.url}
        target="_blank"
        rel="noreferrer"
        className="text-sm font-medium underline-offset-4 hover:underline"
      >
        #{pr.number} · {pr.branch}
      </a>
      <p className="mt-2 text-xs text-zinc-500">
        state: {pr.state} · draft: {pr.draft ? "yes" : "no"} · opened{" "}
        {new Date(pr.opened_at).toLocaleString()}
      </p>
    </Card>
  )
}
