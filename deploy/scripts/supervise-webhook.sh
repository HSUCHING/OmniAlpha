#!/usr/bin/env bash
# Keep deploy webhook on :8702 (host uvicorn + venv). No systemd on this box.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV="${DEPLOY_WEBHOOK_VENV:-$ROOT/.venv-webhook}"
LOG="${DEPLOY_WEBHOOK_LOG:-/tmp/omnialpha-webhook.log}"
PIDFILE="${DEPLOY_WEBHOOK_PID:-/tmp/omnialpha-webhook.pid}"
export DOCKER_HOST="${DOCKER_HOST:-tcp://127.0.0.1:2375}"
export PATH="/home/box/.local/bin:$PATH"

cd "$ROOT"
if [[ -f .env ]]; then set -a; # shellcheck disable=SC1091
  source .env
  set +a
fi
: "${DEPLOY_WEBHOOK_SECRET:?set DEPLOY_WEBHOOK_SECRET in .env}"
export DEPLOY_REPO_DIR="${DEPLOY_REPO_DIR:-$ROOT}"
export DEPLOY_SCRIPT="${DEPLOY_SCRIPT:-$ROOT/deploy/scripts/deploy.sh}"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
PORT="${DEPLOY_WEBHOOK_PORT:-8702}"

if [[ ! -x "$VENV/bin/uvicorn" ]]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r deploy/webhook/requirements.txt
fi

echo $$ > "$PIDFILE"
echo "[supervise-webhook] root=$ROOT port=$PORT venv=$VENV log=$LOG"
while true; do
  echo "[supervise-webhook] $(date -u +%Y-%m-%dT%H:%M:%SZ) starting uvicorn" | tee -a "$LOG"
  "$VENV/bin/uvicorn" deploy.webhook.app:app --host 127.0.0.1 --port "$PORT" --app-dir "$ROOT" >>"$LOG" 2>&1 || true
  echo "[supervise-webhook] $(date -u +%Y-%m-%dT%H:%M:%SZ) exited; restart in 3s" | tee -a "$LOG"
  sleep 3
done
