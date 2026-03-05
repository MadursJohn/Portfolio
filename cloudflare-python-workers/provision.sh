#!/usr/bin/env bash
# provision.sh — Create all required Cloudflare infrastructure.
# Run once before deploying. Requires wrangler CLI + CLOUDFLARE_API_TOKEN set.
#
# Usage:
#   chmod +x provision.sh
#   CLOUDFLARE_API_TOKEN=xxxx ./provision.sh

set -euo pipefail

echo "==> Creating KV namespaces..."
KV_PROD=$(wrangler kv:namespace create ITEMS_KV             --json | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
KV_PREV=$(wrangler kv:namespace create ITEMS_KV --preview   --json | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
KV_STG=$(wrangler kv:namespace create  ITEMS_KV_STAGING     --json | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "   KV prod id     : $KV_PROD"
echo "   KV preview id  : $KV_PREV"
echo "   KV staging id  : $KV_STG"

echo ""
echo "==> Creating Queues..."
wrangler queues create task-queue     || echo "   (task-queue already exists)"
wrangler queues create task-queue-dlq || echo "   (task-queue-dlq already exists)"

echo ""
echo "==> Done. Paste these IDs into each wrangler.toml:"
echo ""
echo "   [[kv_namespaces]] id           = \"$KV_PROD\""
echo "   [[kv_namespaces]] preview_id   = \"$KV_PREV\""
echo "   [env.staging] kv id            = \"$KV_STG\""
echo "   [env.production] kv id         = \"$KV_PROD\""
