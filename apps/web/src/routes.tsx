// Router config. One area per top-level path; details live under /:id.

import { Navigate, createBrowserRouter } from "react-router-dom"

import { App } from "@/app"
import { BacklogList } from "@/pages/backlog/backlog-list"
import { OrgDetail } from "@/pages/orgs/org-detail"
import { OrgsList } from "@/pages/orgs/orgs-list"
import { RunDetail } from "@/pages/runs/run-detail"
import { RunLive } from "@/pages/runs/run-live"
import { RunsList } from "@/pages/runs/runs-list"
import { UsersList } from "@/pages/users/users-list"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/runs" replace /> },
      { path: "runs", element: <RunsList /> },
      { path: "runs/:runId", element: <RunDetail /> },
      { path: "runs/:runId/live", element: <RunLive /> },
      { path: "backlog", element: <BacklogList /> },
      { path: "users", element: <UsersList /> },
      { path: "orgs", element: <OrgsList /> },
      { path: "orgs/:orgId", element: <OrgDetail /> },
    ],
  },
])
