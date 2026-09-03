#!/usr/bin/env bash
# Preferred when compose image build fails (apt/apk mirrors). Uses host docker/git.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
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
pip install -q -r deploy/webhook/requirements.txt
exec uvicorn deploy.webhook.app:app --host 0.0.0.0 --port "$PORT" --app-dir "$ROOT"
