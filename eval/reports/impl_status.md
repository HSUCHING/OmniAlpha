# OmniAlpha impl status (2026-09-03 Asia/Taipei)

## Service
- Compose: `omnialpha-facade/postgres/redis`
- Local: http://127.0.0.1:8700
- Public: https://api.metacognix.xyz
- Brand: `omnialpha`
- G0: `domain/` does not import adapters (ports + `apps/facade/wiring.py`)

## Market × capability

| Market | watch | query | screen | analyze | notes |
|--------|-------|-------|--------|---------|-------|
| CN | PASS tencent | PASS bars/instruments | 501 | 501 | |
| US | PASS yfinance | PASS bars | 501 | 501 | Yahoo may 429 crumb; last quote often still OK |
| CRYPTO | PASS okx | PASS | 501 | 501 | |
| POLY | unsupported on /v1/quotes | prediction routes **501** phase-1 | 501 | 501 | separate path reserved; not advertised implemented |

## Probes
- GET /healthz 200
- GET /health/ready 200 (pg+redis)
- GET /v1/meta/capabilities 200
- Auth 401 / bad prefix 422 / analyze|screen 501
