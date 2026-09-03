# Deploy

- `scalar/` — API docs UI (:8701)
- `webhook/` — HMAC deploy receiver (:8702), hostname `deploy.metacognix.xyz`
- `scripts/deploy.sh` — allowlist `facade` + `scalar` only
- Root compose service: `deploy-webhook`
