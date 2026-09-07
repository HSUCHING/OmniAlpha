#!/usr/bin/env bash
# Allowlist deploy: facade + scalar only. Do not touch postgres/redis volumes.
# Disposable worktree avoids rewriting the live checkout (webhook host process).
set -euo pipefail

TAG="${1:-}"
if [[ ! "$TAG" =~ ^deploy-[A-Za-z0-9._-]+$ ]]; then
  echo "error: tag must match deploy-* (got: ${TAG:-empty})" >&2
  exit 2
fi

LIVE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK_ROOT="${DEPLOY_WORK_ROOT:-/tmp/omnialpha-deploy}"
TREE="$WORK_ROOT/$TAG"
# Pin project: worktree dirname would otherwise spawn a second stack.
# Pass -p on CLI — sudo drops COMPOSE_PROJECT_NAME by default.
PROJECT="${COMPOSE_PROJECT_NAME:-omnialpha}"

echo "[deploy] live=$LIVE_ROOT tag=$TAG worktree=$TREE project=$PROJECT"

mkdir -p "$WORK_ROOT"
if [[ -d "$TREE" ]]; then
  git -C "$LIVE_ROOT" worktree remove --force "$TREE" 2>/dev/null || rm -rf "$TREE"
fi

git -C "$LIVE_ROOT" fetch --tags --force origin
git -C "$LIVE_ROOT" worktree add --force -B "deploy/$TAG" "$TREE" "refs/tags/$TAG"

cleanup() {
  git -C "$LIVE_ROOT" worktree remove --force "$TREE" 2>/dev/null || rm -rf "$TREE"
}
trap cleanup EXIT

cd "$TREE"
SERVICES=(facade scalar)
# Prefer host docker CLI (this box often uses DOCKER_HOST=tcp://127.0.0.1:2375).
if [[ -n "${DOCKER_BIN:-}" ]]; then
  DOCKER=("$DOCKER_BIN")
elif command -v docker >/dev/null 2>&1; then
  DOCKER=(docker)
elif [[ -x /home/box/.local/bin/docker ]]; then
  DOCKER=(/home/box/.local/bin/docker)
elif sudo -n docker version >/dev/null 2>&1; then
  DOCKER=(sudo -n docker)
else
  echo "error: docker CLI not found" >&2
  exit 127
fi
export DOCKER_HOST="${DOCKER_HOST:-tcp://127.0.0.1:2375}"

echo "[deploy] docker=${DOCKER[*]} DOCKER_HOST=$DOCKER_HOST"
echo "[deploy] building: ${SERVICES[*]} (-p $PROJECT)"
"${DOCKER[@]}" compose -p "$PROJECT" build "${SERVICES[@]}"
echo "[deploy] up -d: ${SERVICES[*]} (volumes untouched)"
"${DOCKER[@]}" compose -p "$PROJECT" up -d "${SERVICES[@]}"
echo "[deploy] done"
"${DOCKER[@]}" compose -p "$PROJECT" ps "${SERVICES[@]}" || true
