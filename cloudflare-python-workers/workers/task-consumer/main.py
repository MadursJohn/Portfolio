"""
task-consumer — Cloudflare Queue consumer.

Processes messages sent by task-producer.
Each message is acknowledged on success; failures are automatically
retried by Cloudflare up to the configured max_retries.

Binding in wrangler.toml:
  [[queues.consumers]]
  queue = "task-queue"
  max_batch_size    = 10
  max_retries       = 3
  dead_letter_queue = "task-queue-dlq"
"""

import json


async def on_queue(batch, env):
    """Called by Cloudflare when messages arrive in the queue."""
    results = {"processed": 0, "failed": 0}

    for message in batch.messages:
        try:
            payload = _parse(message.body)
            await _process(payload, env)
            message.ack()
            results["processed"] += 1
        except Exception as exc:
            # Do NOT ack — Cloudflare will retry up to max_retries
            message.retry()
            results["failed"] += 1
            print(f"[task-consumer] Failed job {_job_id(message)}: {exc}")

    print(f"[task-consumer] Batch complete: {results}")


async def _process(payload, env):
    """
    Dispatch task by type.
    Extend this with your own task types.
    """
    task_type = payload.get("type", "unknown")

    if task_type == "store":
        key = payload["key"]
        value = payload["value"]
        await env.ITEMS_KV.put(key, str(value))

    elif task_type == "delete":
        key = payload["key"]
        await env.ITEMS_KV.delete(key)

    elif task_type == "ping":
        pass  # no-op health check task

    else:
        raise ValueError(f"Unknown task type: {task_type!r}")


def _parse(body):
    if isinstance(body, str):
        return json.loads(body)
    return body  # already parsed by Cloudflare runtime


def _job_id(message):
    body = _parse(message.body)
    return body.get("job_id", message.id)
