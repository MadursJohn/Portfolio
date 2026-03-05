"""
demo.py - Local simulation of the Cloudflare Python Workers stack.

Simulates all three workers using Python's built-in http.server:
  - api-worker     -> http://localhost:8001
  - task-producer  -> http://localhost:8002
  - task-consumer  -> runs as background queue processor

No external dependencies required.

Usage:
    python demo.py

Then try:
    curl http://localhost:8001/items
    curl -X POST http://localhost:8001/items/hello -d '"world"'
    curl http://localhost:8001/items/hello
    curl -X POST http://localhost:8002/enqueue -H "Content-Type: application/json" \\
         -d '{"type":"store","key":"queued-key","value":"queued-value"}'
    curl http://localhost:8001/items/queued-key
"""

import json
import threading
import time
import queue
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse


# -- Shared in-memory state (simulates Cloudflare KV + Queue) -----------------

KV_STORE: dict[str, str] = {}
TASK_QUEUE: queue.Queue = queue.Queue()


# -- api-worker simulation -----------------------------------------------------

class ApiWorkerHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"[api-worker]   {fmt % args}")

    def do_GET(self):
        parts = self._path_parts()
        if not parts or parts[0] != "items":
            return self._send(404, {"error": "Not found"})

        if len(parts) == 1:
            # List all keys
            return self._send(200, {"keys": list(KV_STORE.keys()), "count": len(KV_STORE)})

        key = parts[1]
        value = KV_STORE.get(key)
        if value is None:
            return self._send(404, {"error": f"Key '{key}' not found"})
        return self._send(200, {"key": key, "value": value})

    def do_POST(self):
        parts = self._path_parts()
        if not parts or parts[0] != "items" or len(parts) < 2:
            return self._send(400, {"error": "POST /items/{key} required"})

        key = parts[1]
        body = self._read_body()
        KV_STORE[key] = body
        return self._send(201, {"ok": True, "key": key})

    def do_DELETE(self):
        parts = self._path_parts()
        if not parts or parts[0] != "items" or len(parts) < 2:
            return self._send(400, {"error": "DELETE /items/{key} required"})

        key = parts[1]
        KV_STORE.pop(key, None)
        return self._send(200, {"ok": True, "key": key})

    def _path_parts(self):
        path = urlparse(self.path).path.strip("/")
        return [p for p in path.split("/") if p]

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length).decode() if length else ""

    def _send(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# -- task-producer simulation --------------------------------------------------

class TaskProducerHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"[task-producer] {fmt % args}")

    def do_POST(self):
        path = urlparse(self.path).path.strip("/")
        if path != "enqueue":
            return self._send(404, {"error": "POST /enqueue only"})

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode() if length else ""

        try:
            payload = json.loads(raw)
        except Exception:
            return self._send(400, {"error": "Invalid JSON"})

        job_id = str(uuid.uuid4())[:8]
        message = {"job_id": job_id, **payload}
        TASK_QUEUE.put(message)
        print(f"[task-producer] Enqueued job {job_id}: {payload}")

        return self._send(202, {"ok": True, "job_id": job_id})

    def _send(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# -- task-consumer simulation --------------------------------------------------

def task_consumer_loop():
    """Background thread - polls the queue and processes messages."""
    print("[task-consumer] Started, waiting for messages...")
    while True:
        try:
            message = TASK_QUEUE.get(timeout=1)
        except queue.Empty:
            continue

        job_id = message.get("job_id", "?")
        task_type = message.get("type", "unknown")

        try:
            if task_type == "store":
                key, value = message["key"], str(message["value"])
                KV_STORE[key] = value
                print(f"[task-consumer] OK job {job_id}: stored '{key}' = '{value}'")

            elif task_type == "delete":
                KV_STORE.pop(message["key"], None)
                print(f"[task-consumer] OK job {job_id}: deleted '{message['key']}'")

            elif task_type == "ping":
                print(f"[task-consumer] OK job {job_id}: ping ok")

            else:
                raise ValueError(f"Unknown task type: {task_type!r}")

        except Exception as exc:
            print(f"[task-consumer] FAILED job {job_id}: {exc}")

        TASK_QUEUE.task_done()


# -- Startup -------------------------------------------------------------------

if __name__ == "__main__":
    # Start task-consumer as background thread
    consumer = threading.Thread(target=task_consumer_loop, daemon=True)
    consumer.start()

    # Start task-producer on port 8002
    producer_server = HTTPServer(("localhost", 8002), TaskProducerHandler)
    producer_thread = threading.Thread(target=producer_server.serve_forever, daemon=True)
    producer_thread.start()

    print("=" * 60)
    print("  Cloudflare Python Workers - Local Demo")
    print("=" * 60)
    print()
    print("  api-worker    ->  http://localhost:8001")
    print("  task-producer ->  http://localhost:8002")
    print("  task-consumer ->  background thread (watching queue)")
    print()
    print("  Try these commands:")
    print('  curl http://localhost:8001/items')
    print('  curl -X POST http://localhost:8001/items/hello -d \'"world"\'')
    print('  curl http://localhost:8001/items/hello')
    print('  curl -X POST http://localhost:8002/enqueue \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"type":"store","key":"job-result","value":"done"}\'')
    print('  curl http://localhost:8001/items/job-result')
    print()
    print("  Press Ctrl+C to stop.")
    print()

    # Start api-worker on port 8001 (blocks main thread)
    api_server = HTTPServer(("localhost", 8001), ApiWorkerHandler)
    try:
        api_server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
