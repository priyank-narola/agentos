#!/usr/bin/env bash
# Starts the pinned Paperclip source as a local-only Workforce Studio sidecar.
# It deliberately has no AgentOS database connection, no provider keys, and no
# external connector configuration.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPERCLIP_SOURCE="$REPO_ROOT/vendor/paperclip-upstream"
COMPOSE_OVERRIDE="$REPO_ROOT/integrations/paperclip/docker-compose.agentos-local.yml"

if [[ ! -f "$PAPERCLIP_SOURCE/docker/docker-compose.quickstart.yml" || ! -f "$COMPOSE_OVERRIDE" ]]; then
  echo "Paperclip source is unavailable. Run: git submodule update --init --recursive" >&2
  exit 1
fi

export PAPERCLIP_PORT="${PAPERCLIP_PORT:-3100}"
export PAPERCLIP_DATA_DIR="${PAPERCLIP_DATA_DIR:-$REPO_ROOT/.agentos-local/paperclip}"
export PAPERCLIP_PUBLIC_URL="${PAPERCLIP_PUBLIC_URL:-http://localhost:$PAPERCLIP_PORT}"
export PAPERCLIP_DEPLOYMENT_MODE="${PAPERCLIP_DEPLOYMENT_MODE:-local_trusted}"
export PAPERCLIP_DEPLOYMENT_EXPOSURE="${PAPERCLIP_DEPLOYMENT_EXPOSURE:-private}"

# A caller may supply a stable local secret to preserve sessions between runs.
# The generated fallback intentionally only supports an ephemeral local demo.
if [[ -z "${BETTER_AUTH_SECRET:-}" ]]; then
  BETTER_AUTH_SECRET="$(openssl rand -hex 32)"
  export BETTER_AUTH_SECRET
  echo "Using an ephemeral local session secret; supply BETTER_AUTH_SECRET to retain sessions."
fi

mkdir -p "$PAPERCLIP_DATA_DIR"
echo "Starting Workforce Studio at $PAPERCLIP_PUBLIC_URL"
echo "Data directory: $PAPERCLIP_DATA_DIR"
echo "Mode: $PAPERCLIP_DEPLOYMENT_MODE / $PAPERCLIP_DEPLOYMENT_EXPOSURE"

exec docker compose \
  -f "$PAPERCLIP_SOURCE/docker/docker-compose.quickstart.yml" \
  -f "$COMPOSE_OVERRIDE" \
  --project-directory "$PAPERCLIP_SOURCE/docker" \
  up --build
