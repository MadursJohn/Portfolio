# cloudflare-python-workers

> A production-ready Cloudflare Workers monorepo in Python — demonstrating
> Workers, KV storage, Queues, multi-environment deployment, and a full
> GitHub Actions CI/CD pipeline.

![Deploy](https://github.com/MadursJohn/Freelance_Portfolio/actions/workflows/cloudflare-python-workers.yml/badge.svg)
![Python](https://img.shields.io/badge/python-workers-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Architecture

```
                        ┌──────────────────────────────────────────┐
                        │           Cloudflare Edge Network         │
                        │                                           │
  HTTP Request          │  ┌─────────────────┐                     │
─────────────────────►  │  │   api-worker    │ ◄──► KV (ITEMS_KV)  │
  GET/POST/DELETE /api  │  └─────────────────┘                     │
                        │                                           │
  HTTP Request          │  ┌─────────────────┐                     │
─────────────────────►  │  │  task-producer  │ ──► Queue           │
  POST /enqueue         │  └─────────────────┘      │              │
                        │                            │              │
                        │  ┌─────────────────┐       │              │
                        │  │  task-consumer  │ ◄─────┘              │
                        │  │  (queue-driven) │ ──► KV (ITEMS_KV)   │
                        │  └─────────────────┘                     │
                        └──────────────────────────────────────────┘
```

## Services

| Worker | Trigger | Cloudflare bindings | Purpose |
|---|---|---|---|
| `api-worker` | HTTP | KV, Queue (producer) | CRUD API over KV storage |
| `task-producer` | HTTP | Queue (producer) | Enqueue background jobs |
| `task-consumer` | Queue | KV | Process jobs off the queue |

---

## CI/CD pipeline

```
push to main
     │
     ▼
┌─────────┐    ┌──────────────┐    ┌──────────────────┐
│  Lint   │──► │   Validate   │──► │  Deploy staging  │
│ flake8  │    │ wrangler     │    │  (all 3 workers) │
└─────────┘    │ --dry-run    │    └──────────────────┘
               └──────────────┘

push tag v*.*.*
     │
     ▼
┌─────────┐    ┌──────────────┐    ┌──────────────────────┐
│  Lint   │──► │   Validate   │──► │  Deploy production   │
└─────────┘    └──────────────┘    │  (all 3 workers)     │
                                   └──────────────────────┘
```

- **Staging** — auto-deployed on every push to `main`
- **Production** — deployed only on version tags (`v1.2.3`)
- **PRs** — lint + dry-run validation only, no deploy

---

## Repository structure

```
cloudflare-python-workers/
├── .github/
│   └── workflows/
│       └── deploy.yml          # Lint → validate → deploy pipeline
├── workers/
│   ├── api-worker/
│   │   ├── main.py             # CRUD HTTP handler + KV read/write
│   │   └── wrangler.toml       # Bindings: KV + Queue producer
│   ├── task-producer/
│   │   ├── main.py             # POST /enqueue → sends to Queue
│   │   └── wrangler.toml       # Binding: Queue producer
│   └── task-consumer/
│       ├── main.py             # Queue consumer → processes + writes KV
│       └── wrangler.toml       # Bindings: Queue consumer + KV
├── provision.sh                # One-time infra setup (KV + Queue creation)
└── README.md
```

---

## Prerequisites

- [Node.js 20+](https://nodejs.org/) (for wrangler CLI)
- [wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/)
- A Cloudflare account with Workers + KV + Queues enabled

```bash
npm install -g wrangler
wrangler login
```

---

## First-time setup

### 1. Provision infrastructure

Run once to create the KV namespace and Queues on your Cloudflare account:

```bash
CLOUDFLARE_API_TOKEN=your_token ./provision.sh
```

Copy the output IDs into each `workers/*/wrangler.toml` under `[[kv_namespaces]]`.

### 2. Add GitHub secret

In your repo: **Settings → Secrets → Actions → New repository secret**

| Secret | Value |
|---|---|
| `CLOUDFLARE_API_TOKEN` | API token with `Workers Scripts:Edit`, `Workers KV Storage:Edit`, `Workers Queues:Edit` |

### 3. Deploy

```bash
# Deploy to staging
cd workers/api-worker    && wrangler deploy --env staging
cd workers/task-producer && wrangler deploy --env staging
cd workers/task-consumer && wrangler deploy --env staging

# Deploy to production
cd workers/api-worker    && wrangler deploy --env production
# ... repeat for each worker
```

Or push to `main` — GitHub Actions handles it automatically.

---

## Local development

```bash
# Run a worker locally (hot reload)
cd workers/api-worker
wrangler dev

# Test the API
curl http://localhost:8787/items
curl -X POST http://localhost:8787/items/hello -d '"world"'
curl http://localhost:8787/items/hello
curl -X DELETE http://localhost:8787/items/hello
```

---

## API reference

### `api-worker`

| Method | Path | Description |
|---|---|---|
| `GET` | `/items` | List all KV keys |
| `GET` | `/items/{key}` | Read a value |
| `POST` | `/items/{key}` | Write a value (body = raw string) |
| `DELETE` | `/items/{key}` | Delete a key |

### `task-producer`

| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/enqueue` | `{"type": "store", "key": "x", "value": "y"}` | Enqueue a task |

**Task types supported by `task-consumer`:**

| type | Required fields | Effect |
|---|---|---|
| `store` | `key`, `value` | Writes `value` to KV under `key` |
| `delete` | `key` | Deletes `key` from KV |
| `ping` | — | No-op health check |

---

## Background

Built to demonstrate Cloudflare Workers deployment patterns for real client projects —
covering multi-service monorepo configuration, KV storage, Queue integration,
and automated CI/CD with environment promotion.

---

## License

MIT — use freely, adapt for your infrastructure.
