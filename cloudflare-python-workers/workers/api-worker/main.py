"""
api-worker — HTTP API backed by Cloudflare KV storage.

Endpoints:
  GET  /items          → list all keys in KV
  GET  /items/{key}    → read a value from KV
  POST /items/{key}    → write a value to KV
  DELETE /items/{key}  → delete a value from KV
"""

from js import Response, Headers
import json


async def on_fetch(request, env):
    url = request.url
    method = request.method.upper()

    # Split path: /items/{key}
    path = url.split("?")[0].split("/")
    path = [p for p in path if p and p not in ("http:", "https:", request.headers.get("host", ""))]

    if not path or path[0] != "items":
        return _json_response({"error": "Not found"}, status=404)

    key = path[1] if len(path) > 1 else None

    if method == "GET" and not key:
        return await _list_items(env)

    if method == "GET" and key:
        return await _get_item(env, key)

    if method == "POST" and key:
        body = await request.text()
        return await _put_item(env, key, body)

    if method == "DELETE" and key:
        return await _delete_item(env, key)

    return _json_response({"error": "Method not allowed"}, status=405)


async def _list_items(env):
    result = await env.ITEMS_KV.list()
    keys = [k.name for k in result.keys]
    return _json_response({"keys": keys, "count": len(keys)})


async def _get_item(env, key):
    value = await env.ITEMS_KV.get(key)
    if value is None:
        return _json_response({"error": f"Key '{key}' not found"}, status=404)
    return _json_response({"key": key, "value": value})


async def _put_item(env, key, body):
    await env.ITEMS_KV.put(key, body)
    return _json_response({"ok": True, "key": key}, status=201)


async def _delete_item(env, key):
    await env.ITEMS_KV.delete(key)
    return _json_response({"ok": True, "key": key})


def _json_response(data, status=200):
    headers = Headers.new({"content-type": "application/json"}.items())
    return Response.new(json.dumps(data), status=status, headers=headers)
