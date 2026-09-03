#!/usr/bin/env bash
# Allowlist deploy: facade + scalar only. Do not touch postgres/redis volumes.
set -euo pipefail

TAG="${1:-}"
if [[ ! "$TAG" =~ ^deploy-[A-Za-z0-9._-]+$ ]]; then
  echo "error: tag must match deploy-* (got: ${TAG:-empty})" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
echo "[deploy] root=$ROOT tag=$TAG"

git fetch --tags --force origin
git checkout -f "$TAG"

# Fixed allowlist — webhook must NOT choose services
SERVICES=(facade scalar)
# Host box user is not in docker group; passwordless sudo is available.
DOCKER=(sudo -n docker)
echo "[deploy] building: ${SERVICES[*]}"
"${DOCKER[@]}" compose build "${SERVICES[@]}"
echo "[deploy] up -d: ${SERVICES[*]} (volumes untouched)"
"${DOCKER[@]}" compose up -d "${SERVICES[@]}"
echo "[deploy] done"
"${DOCKER[@]}" compose ps "${SERVICES[@]}" || true
