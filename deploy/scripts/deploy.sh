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
echo "[deploy] building: ${SERVICES[*]}"
docker compose build "${SERVICES[@]}"
echo "[deploy] up -d: ${SERVICES[*]} (volumes untouched)"
docker compose up -d "${SERVICES[@]}"
echo "[deploy] done"
docker compose ps "${SERVICES[@]}" || true
