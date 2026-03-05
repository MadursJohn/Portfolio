"""
record_demo.py — Clean, slow-paced demo runner for screen recording.

Run this WHILE screen recording. It prints each step with a pause so
the viewer can read it, then fires the actual HTTP calls.

Usage:
    1. Start screen recording (Win + G or ShareX)
    2. python record_demo.py
    3. Stop recording when it prints "Done."
"""

import time
import json
import urllib.request
import urllib.error
import subprocess
import sys
import os

W  = "\033[0m"       # reset
B  = "\033[94m"      # blue  - prompts
G  = "\033[92m"      # green - success
Y  = "\033[93m"      # yellow - labels
C  = "\033[96m"      # cyan  - values
DIM = "\033[2m"      # dim   - comments


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause(n=1.8):
    time.sleep(n)


def header(text):
    width = 60
    print()
    print(Y + "=" * width + W)
    print(Y + f"  {text}" + W)
    print(Y + "=" * width + W)
    print()
    pause(1.2)


def cmd(text):
    print(B + "PS> " + W + text)
    pause(1.0)


def resp(data: dict):
    for k, v in data.items():
        print(f"    {C}{k}{W} : {G}{v}{W}")
    print()
    pause(1.5)


def note(text):
    print(DIM + f"    # {text}" + W)
    pause(0.8)


def get(path) -> dict:
    req = urllib.request.urlopen(f"http://localhost:8001{path}")
    return json.loads(req.read())


def post_api(path, body: str) -> dict:
    data = body.encode()
    req = urllib.request.Request(
        f"http://localhost:8001{path}",
        data=data,
        method="POST",
    )
    resp_raw = urllib.request.urlopen(req)
    return json.loads(resp_raw.read())


def delete(path) -> dict:
    req = urllib.request.Request(
        f"http://localhost:8001{path}",
        method="DELETE",
    )
    resp_raw = urllib.request.urlopen(req)
    return json.loads(resp_raw.read())


def enqueue(payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "http://localhost:8002/enqueue",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    resp_raw = urllib.request.urlopen(req)
    return json.loads(resp_raw.read())


# ── Check servers are up ──────────────────────────────────────────────────────

try:
    urllib.request.urlopen("http://localhost:8001/items")
    urllib.request.urlopen("http://localhost:8002/enqueue",
                           data=b'{"type":"ping"}',
                           timeout=1)
except Exception:
    print("\033[91mERROR: demo.py is not running.\033[0m")
    print("Start it first:  python demo.py")
    sys.exit(1)


# ── Recording starts here ─────────────────────────────────────────────────────

clear()

header("Cloudflare Python Workers — Live Demo")
note("3 workers: api-worker | task-producer | task-consumer")
note("Running locally via demo.py (mirrors real Cloudflare behaviour)")
pause(2)

# --- Section 1: api-worker CRUD ---
header("1 / 3  api-worker  —  CRUD over KV Storage")

cmd("Invoke-RestMethod http://localhost:8001/items")
resp(get("/items"))

cmd("Invoke-RestMethod -Method POST http://localhost:8001/items/greeting -Body '\"hello world\"'")
resp(post_api("/items/greeting", '"hello world"'))

cmd("Invoke-RestMethod http://localhost:8001/items/greeting")
resp(get("/items/greeting"))

cmd("Invoke-RestMethod http://localhost:8001/items")
resp(get("/items"))

# --- Section 2: Queue flow ---
header("2 / 3  task-producer + task-consumer  —  Async Queue Flow")

cmd("Invoke-RestMethod -Method POST http://localhost:8002/enqueue \\")
print(B + "      " + W + "-Body '{\"type\":\"store\",\"key\":\"order-99\",\"value\":\"shipped\"}'")
pause(1)
r = enqueue({"type": "store", "key": "order-99", "value": "shipped"})
resp(r)

note("task-consumer picks it up from the Queue and writes to KV...")
pause(2)

cmd("Invoke-RestMethod http://localhost:8001/items/order-99")
resp(get("/items/order-99"))

cmd("Invoke-RestMethod -Method POST http://localhost:8002/enqueue -Body '{\"type\":\"ping\"}'")
r2 = enqueue({"type": "ping"})
resp(r2)
pause(0.5)

# --- Section 3: Cleanup ---
header("3 / 3  Cleanup  —  DELETE + queue delete task")

cmd("Invoke-RestMethod -Method DELETE http://localhost:8001/items/greeting")
resp(delete("/items/greeting"))

cmd("Invoke-RestMethod -Method POST http://localhost:8002/enqueue \\")
print(B + "      " + W + "-Body '{\"type\":\"delete\",\"key\":\"order-99\"}'")
r3 = enqueue({"type": "delete", "key": "order-99"})
pause(1)
resp(r3)
pause(1.5)

cmd("Invoke-RestMethod http://localhost:8001/items")
resp(get("/items"))

# --- Done ---
print(Y + "=" * 60 + W)
print(G + "  All workers verified. Full source on GitHub." + W)
print(Y + "  github.com/MadursJohn/Freelance_Portfolio" + W)
print(Y + "=" * 60 + W)
print()
pause(3)
