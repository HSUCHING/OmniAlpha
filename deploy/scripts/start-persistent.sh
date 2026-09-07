#!/usr/bin/env bash
# Start persistent host services: cloudflared + deploy webhook (+ optional scalar).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
mkdir -p /tmp

start_one() {
  local name="$1" pidfile="$2" cmd="$3"
  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "[ok] $name already running pid=$(cat "$pidfile")"
    return 0
  fi
  # shellcheck disable=SC2086
  nohup bash -c "$cmd" >/dev/null 2>&1 &
  sleep 1
  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "[started] $name pid=$(cat "$pidfile")"
  else
    echo "[warn] $name pidfile missing; check logs" >&2
  fi
}

# If a bare cloudflared is already up, leave it; else supervise.
if pgrep -x cloudflared >/dev/null 2>&1; then
  echo "[ok] cloudflared already running"
else
  start_one cloudflared /tmp/cloudflared-supervise.pid "$ROOT/deploy/scripts/supervise-cloudflared.sh"
fi

start_one webhook /tmp/omnialpha-webhook.pid "$ROOT/deploy/scripts/supervise-webhook.sh"

# Scalar static docs on 8701 if free
if ss -lntp 2>/dev/null | rg -q ':8701'; then
  echo "[ok] :8701 already listening"
else
  WWW="$ROOT/deploy/scalar-www"
  mkdir -p "$WWW"
  cp -f "$ROOT/deploy/scalar/index.html" "$WWW/"
  cp -f "$ROOT/contracts/openapi.yaml" "$WWW/"
  nohup python3 -m http.server 8701 --bind 127.0.0.1 >/tmp/scalar-http.log 2>&1 &
  echo "[started] scalar-http pid=$!"
fi

curl -sS -m 3 http://127.0.0.1:8702/healthz || true
echo
curl -sS -m 3 http://127.0.0.1:8700/healthz || true
echo
