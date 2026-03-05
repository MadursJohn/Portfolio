# Cloudflare Python Workers — API Reference

**GitHub:** https://github.com/MadursJohn/Freelance_Portfolio/tree/main/cloudflare-python-workers

---

## api-worker  `http://<your-worker>.workers.dev`

Handles HTTP CRUD requests, reading and writing values in Cloudflare KV Storage.

| Method | Path | Body | Response | Description |
|---|---|---|---|---|
| `GET` | `/items` | — | `{"keys": [...], "count": N}` | List all KV keys |
| `GET` | `/items/{key}` | — | `{"key": "...", "value": "..."}` | Read a value |
| `POST` | `/items/{key}` | raw string | `{"ok": true, "key": "..."}` | Write a value |
| `DELETE` | `/items/{key}` | — | `{"ok": true, "key": "..."}` | Delete a key |

**Example:**
```
POST /items/greeting
Body: "hello world"

→ {"ok": true, "key": "greeting"}
```

---

## task-producer  `http://<your-worker>.workers.dev`

Accepts job payloads over HTTP and pushes them onto a Cloudflare Queue.
The queue is processed asynchronously by `task-consumer`.

| Method | Path | Content-Type | Description |
|---|---|---|---|
| `POST` | `/enqueue` | `application/json` | Enqueue a background task |

**Request body:**

```json
{
  "type": "store",
  "key": "my-key",
  "value": "my-value"
}
```

**Response:**

```json
{"ok": true, "job_id": "f692b762"}
```

---

## task-consumer  *(queue-triggered — no HTTP endpoint)*

Triggered automatically by Cloudflare when messages arrive on the Queue.
Processes each message and writes results back to KV.

### Supported task types

| `type` | Required fields | Effect |
|---|---|---|
| `store` | `key`, `value` | Writes `value` to KV under `key` |
| `delete` | `key` | Deletes `key` from KV |
| `ping` | — | No-op health check, acknowledges message |

Messages that fail processing are **retried automatically** by Cloudflare Queues.
Messages that succeed are **acknowledged** and removed from the queue.

---

## Cloudflare bindings

| Worker | Binding name | Type |
|---|---|---|
| `api-worker` | `ITEMS_KV` | KV Namespace |
| `task-producer` | `TASK_QUEUE` | Queue (producer) |
| `task-consumer` | `TASK_QUEUE` | Queue (consumer) |
| `task-consumer` | `ITEMS_KV` | KV Namespace |

---

## Environment promotion

| Event | Environment |
|---|---|
| Push to `main` branch | Staging |
| Push tag `v1.2.3` | Production |
| Pull request | Lint + dry-run only |

---

*Delivered with full source code, wrangler configuration, GitHub Actions CI/CD, and setup guide.*
