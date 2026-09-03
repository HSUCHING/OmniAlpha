# Deploy

- `scalar/` — API docs UI (:8701)
- `webhook/` — HMAC deploy receiver (:8702), hostname `deploy.metacognix.xyz`
- `scripts/deploy.sh` — allowlist `facade` + `scalar` only
- `scripts/run-webhook-host.sh` — **preferred** host uvicorn (no image build)
- `ci/deploy.yml` — GitHub Actions template (needs `workflow` scope to place under `.github/workflows/`)
- Root compose service: `deploy-webhook` (optional; Dockerfile uses docker:27-cli + apk)
