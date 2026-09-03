#!/usr/bin/env bash
# Allowlist deploy: facade + scalar only. Do not touch postgres/redis volumes.
# Uses a disposable worktree so we never rewrite the live checkout (webhook/host scripts).
set -euo pipefail

TAG="${1:-}"
if [[ ! "$TAG" =~ ^deploy-[A-Za-z0-9._-]+$ ]]; then
  echo "error: tag must match deploy-* (got: ${TAG:-empty})" >&2
  exit 2
fi

LIVE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK_ROOT="${DEPLOY_WORK_ROOT:-/tmp/omnialpha-deploy}"
TREE="$WORK_ROOT/$TAG"
# Keep updating the existing stack (omnialpha-*), not a new project named after the worktree dir.
PROJECT="${COMPOSE_PROJECT_NAME:-omnialpha}"
# Host box user is not in docker group; passwordless sudo is available.
DOCKER=(sudo -n docker)

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
# Fixed allowlist — webhook must NOT choose services
SERVICES=(facade scalar)
echo "[deploy] building: ${SERVICES[*]}"
COMPOSE_PROJECT_NAME="$PROJECT" "${DOCKER[@]}" compose build "${SERVICES[@]}"
echo "[deploy] up -d: ${SERVICES[*]} (volumes untouched)"
COMPOSE_PROJECT_NAME="$PROJECT" "${DOCKER[@]}" compose up -d "${SERVICES[@]}"
echo "[deploy] done"
COMPOSE_PROJECT_NAME="$PROJECT" "${DOCKER[@]}" compose ps "${SERVICES[@]}" || true
