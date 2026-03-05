"""
task-producer — HTTP endpoint that enqueues background tasks.

POST /enqueue
  Body: JSON payload describing the task
  → sends message to Cloudflare Queue → returns job ID
"""

from js import Response, Headers, crypto
import json


async def on_fetch(request, env):
    if request.method.upper() != "POST":
        return _json_response({"error": "POST only"}, status=405)

    try:
        body = await request.text()
        payload = json.loads(body)
    except Exception:
        return _json_response({"error": "Invalid JSON body"}, status=400)

    job_id = _generate_id()
    message = {"job_id": job_id, **payload}

    await env.TASK_QUEUE.send(message)

    return _json_response({"ok": True, "job_id": job_id}, status=202)


def _generate_id():
    """Generate a short random job ID using the Web Crypto API."""
    buf = crypto.getRandomValues(__builtins__["bytearray"](8))
    return "".join(f"{b:02x}" for b in buf)


def _json_response(data, status=200):
    headers = Headers.new({"content-type": "application/json"}.items())
    return Response.new(json.dumps(data), status=status, headers=headers)
