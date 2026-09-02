# OmniAlpha 场景矩阵报告

- BASE(local): `http://127.0.0.1:8700`
- BASE(public): `https://api.metacognix.xyz`
- KEY: `***`
- MCP: `up`
- Totals: PASS=27 FAIL=0 SKIP=18

## 四市场 × 四能力（HTTP 单元格）

| market \ capability | watch | query | screen | analyze |
|---|---|---|---|---|
| CN | PASS | PASS | SKIP | SKIP |
| US | SKIP | PASS | SKIP | SKIP |
| CRYPTO | SKIP | PASS | SKIP | SKIP |
| POLY | SKIP | SKIP | SKIP | SKIP |

## 明细

| id | market | capability | channel | verdict | detail |
|---|---|---|---|---|---|
| G2-local-healthz | - | - | HTTP | **PASS** | status=200 items=0 |
| G2b-public-healthz | - | - | HTTP | **SKIP** | soft status=403 want=200 |
| M-CN-watch | CN | watch | HTTP | **PASS** | status=200 items=1 |
| M-CN-watch | CN | watch | MCP | **PASS** | status=200 items=1 |
| M-CN-watch | CN | watch | HTTP↔MCP | **PASS** | key fields match (as_of tolerance 5s) |
| M-CN-query | CN | query | HTTP | **PASS** | status=200 items=4 |
| M-CN-query | CN | query | MCP | **PASS** | status=200 items=1 |
| M-CN-query-bars | CN | query | HTTP | **PASS** | status=200 items=5 |
| M-CN-query-bars | CN | query | MCP | **PASS** | status=200 items=5 |
| M-CN-query-bars | CN | query | HTTP↔MCP | **PASS** | key fields match (as_of tolerance 5s) |
| M-CN-screen | CN | screen | HTTP | **SKIP** | N/A-phase1 status=404 |
| M-CN-analyze | CN | analyze | HTTP | **SKIP** | N/A-phase1 status=404 |
| M-US-watch | US | watch | HTTP | **SKIP** | adapter not implemented: US:AAPL: market 'US' quote adapter not implemented in phase-1 |
| M-US-watch | US | watch | MCP | **SKIP** | adapter not implemented: US:AAPL: market 'US' quote adapter not implemented in phase-1 |
| M-US-query | US | query | HTTP | **PASS** | status=200 items=2 |
| M-US-query | US | query | MCP | **PASS** | status=200 items=1 |
| M-US-screen | US | screen | HTTP | **SKIP** | N/A-phase1 status=404 |
| M-US-analyze | US | analyze | HTTP | **SKIP** | N/A-phase1 status=404 |
| M-CRYPTO-watch | CRYPTO | watch | HTTP | **SKIP** | adapter not implemented: CRYPTO:BTCUSDT: market 'CRYPTO' quote adapter not implemented in phase-1 |
| M-CRYPTO-watch | CRYPTO | watch | MCP | **SKIP** | adapter not implemented: CRYPTO:BTCUSDT: market 'CRYPTO' quote adapter not implemented in phase-1 |
| M-CRYPTO-query | CRYPTO | query | HTTP | **PASS** | status=200 items=2 |
| M-CRYPTO-query | CRYPTO | query | MCP | **PASS** | status=200 items=1 |
| M-CRYPTO-screen | CRYPTO | screen | HTTP | **SKIP** | N/A-phase1 status=404 |
| M-CRYPTO-analyze | CRYPTO | analyze | HTTP | **SKIP** | N/A-phase1 status=404 |
| M-POLY-watch | POLY | watch | HTTP | **SKIP** | adapter not implemented: POLY:DUMMY: market 'POLY' quote adapter not implemented in phase-1 |
| M-POLY-watch | POLY | watch | MCP | **SKIP** | adapter not implemented: POLY:DUMMY: market 'POLY' quote adapter not implemented in phase-1 |
| M-POLY-query | POLY | query | HTTP | **SKIP** | empty result (no seed) |
| M-POLY-screen | POLY | screen | HTTP | **SKIP** | N/A-phase1 status=404 |
| M-POLY-analyze | POLY | analyze | HTTP | **SKIP** | N/A-phase1 status=404 |
| S1 | CN | query | HTTP | **PASS** | status=200 items=1 |
| S1 | CN | query | MCP | **PASS** | status=200 items=1 |
| S2 | CN | watch | HTTP | **PASS** | status=200 items=1 |
| S2 | CN | watch | MCP | **PASS** | status=200 items=1 |
| S2 | CN | watch | HTTP↔MCP | **PASS** | key fields match (as_of tolerance 5s) |
| S3 | CN | query | HTTP | **PASS** | status=200 items=5 |
| S3 | CN | query | MCP | **PASS** | status=200 items=5 |
| S3 | CN | query | HTTP↔MCP | **PASS** | key fields match (as_of tolerance 5s) |
| S4 | CN | watch | HTTP | **PASS** | status=200 items=2 |
| S4 | CN | watch | MCP | **PASS** | status=200 items=2 |
| S5 | US | query | HTTP | **PASS** | status=200 items=2 |
| S6 | - | protocol | HTTP | **PASS** | status=422 items=0 |
| S7 | - | auth | HTTP | **PASS** | status=401 items=0 |
| S8 | - | analyze | HTTP | **PASS** | status=404 |
| S9 | - | watch | - | **SKIP** | phase2 |
| S14 | - | auth | - | **SKIP** | phase2 |
