---
tracker:
  kind: linear
  api_key: $LINEAR_API_KEY
  project_slug: ai-platform
  active_states: [Todo, "In Progress"]
  terminal_states: [Done, Cancelled]

polling:
  interval_ms: 30000

workspace:
  root: ~/symphony_workspaces

hooks:
  after_create: |
    npm install
  before_run: |
    npm run typecheck
  after_run: |
    rm -rf node_modules/.cache

agent:
  kind: claude_code
  mode: subscription
  timeout_ms: 1800000
  max_turns: 20

claude_code:
  command: claude
  api_model: claude-sonnet-4-6
  permission_mode: acceptEdits
  allowed_tools: "Read,Edit,Write,Bash"
  turn_timeout_ms: 600000
  stall_timeout_ms: 120000

sdd:
  spec_required: true
  plan_required: true
  approval_via: cli

harness:
  ci_command: npm run ci
  coverage:
    enabled: true
    threshold_new_lines: 80
    tool: c8
  complexity:
    enabled: true
    max_cyclomatic: 15
    max_file_loc: 300
    tool: ts-complex
  self_review:
    enabled: true
    rubric_path: .symphony/rubric.md

pr:
  base_branch: main
  draft: true
  labels: [agent-generated]

retry:
  max_attempts: 3
  continuation_delay_ms: 1000
  failure_base_ms: 10000
  max_backoff_ms: 600000
  jitter_ratio: 0.05

mcp_servers:
  linear:
    command: npx
    args: ["@linear/mcp-server", "--mcp-stdio"]
    env:
      LINEAR_API_KEY: $LINEAR_API_KEY
---

# Agent Prompt

You are a Symphony agent working on issue `{{ issue.identifier }}`: {{ issue.title }}.

## Constraints

- Stay within the approved SPEC and plan.
- Never modify files outside this worktree.
