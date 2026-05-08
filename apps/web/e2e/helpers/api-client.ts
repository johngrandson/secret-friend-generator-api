// Thin fetch wrapper for E2E seed/teardown.
//
// We talk to the backend directly (NOT through the Vite proxy) so seed
// helpers don't need a running browser context. The X-Approver-Id header is
// injected on every request to mirror what the SPA does.

const BACKEND_URL = process.env.E2E_BACKEND_URL ?? "http://localhost:8765"
const APPROVER_ID = process.env.E2E_APPROVER_ID ?? "e2e-approver"

export interface RunSummary {
  id: string
  issue_id: string
  status: string
  attempt: number
  created_at: string
}

class ApiError extends Error {
  constructor(
    public status: number,
    public method: string,
    public path: string,
    public bodyText: string,
  ) {
    super(`${method} ${path} → ${status}: ${bodyText.slice(0, 200)}`)
    this.name = "ApiError"
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-Approver-Id": APPROVER_ID,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) {
    throw new ApiError(res.status, method, path, await res.text())
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export const apiClient = {
  createRun: (issueId: string) =>
    request<RunSummary>("POST", "/runs/", { issue_id: issueId }),

  listRuns: (limit = 50, offset = 0) =>
    request<RunSummary[]>("GET", `/runs/?limit=${limit}&offset=${offset}`),

  getRun: (runId: string) => request<RunSummary>("GET", `/runs/${runId}`),

  deleteRun: (runId: string) => request<void>("DELETE", `/runs/${runId}`),
}

export { ApiError, BACKEND_URL, APPROVER_ID }
