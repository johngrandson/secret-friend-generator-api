# Frontend E2E tests (Playwright)

Tests live in `apps/web/e2e/` and run against the **real backend** (FastAPI on
`:8765`, Redis on `:6380`). No mocks, no service workers.

## Layout

```
e2e/
├── fixtures/test-base.ts        # extends Playwright `test` with seed helpers
├── helpers/
│   ├── api-client.ts            # fetch wrapper for /runs CRUD
│   ├── seed.ts                  # createRun + publish to Redis Pub/Sub
│   └── wait.ts                  # async polling utilities
├── pages/                       # Page Objects (POM)
├── tests/                       # *.spec.ts
└── global-setup.ts              # health-check backend + redis before suite
```

## Prerequisites

```bash
# 1. Postgres + Redis (one-time)
docker compose -f docker/docker-compose.yml up -d

# 2. Backend, Celery worker/beat, Vite (one terminal)
./dev.sh
```

## Running

```bash
cd apps/web

# Install Chromium (one-time)
npx playwright install chromium

# Headless
npm run test:e2e

# Interactive UI mode
npm run test:e2e:ui

# Headed (browser visible)
npm run test:e2e:headed

# Filter by name
npm run test:e2e -- --grep "reconnect"
```

Artifacts (HTML report, traces, screenshots) land in `playwright-report/` and
`test-results/`.

## Environment overrides

| Variable             | Default                           | Notes                       |
| -------------------- | --------------------------------- | --------------------------- |
| `E2E_BACKEND_URL`    | `http://localhost:8765`           | uvicorn API                 |
| `E2E_FRONTEND_URL`   | `http://localhost:5173`           | Vite dev server             |
| `E2E_REDIS_URL`      | `redis://localhost:6380/0`        | Pub/Sub for SSE seed        |
| `E2E_APPROVER_ID`    | `e2e-approver`                    | `X-Approver-Id` header      |

## Troubleshooting

- **"Backend not reachable at …"** → `dev.sh` not running, or Postgres/Redis
  not started. Follow Prerequisites.
- **SSE tests time out on `live`** → Redis URL mismatch between API and tests.
  Verify `CELERY_BROKER_URL` in `.env` matches `E2E_REDIS_URL`.
- **Tests interfere with each other** → suite runs serially (`workers: 1`,
  `fullyParallel: false`). Each test creates a unique `issue_id` and cleans up
  in afterEach via the `trackedRunIds` fixture.
