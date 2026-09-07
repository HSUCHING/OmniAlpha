#!/usr/bin/env bash
# Keep Cloudflare tunnel connector alive (api/apidoc/deploy hostnames).
set -euo pipefail
LOG="${CF_TUNNEL_LOG:-/tmp/cloudflared.log}"
ENV_FILE="${CF_TUNNEL_ENV:-/workspace/cloudflare/tunnel.env}"
BIN="${CLOUDFLARED_BIN:-/workspace/bin/cloudflared}"
PIDFILE="${CF_TUNNEL_PID:-/tmp/cloudflared-supervise.pid}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "missing $ENV_FILE" >&2
  exit 1
fi
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
: "${TUNNEL_TOKEN:?TUNNEL_TOKEN missing in $ENV_FILE}"

echo $$ > "$PIDFILE"
echo "[supervise-cloudflared] bin=$BIN log=$LOG"
while true; do
  echo "[supervise-cloudflared] $(date -u +%Y-%m-%dT%H:%M:%SZ) starting" | tee -a "$LOG"
  "$BIN" tunnel --no-autoupdate run --token "$TUNNEL_TOKEN" >>"$LOG" 2>&1 || true
  echo "[supervise-cloudflared] $(date -u +%Y-%m-%dT%H:%M:%SZ) exited; restart in 5s" | tee -a "$LOG"
  sleep 5
done
