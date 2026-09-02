# OmniAlpha 场景矩阵报告

- BASE(local): `http://127.0.0.1:8700`
- BASE(public): `https://api.metacognix.xyz`
- KEY: `***`
- MCP: `up`
- Totals: PASS=36 FAIL=0 SKIP=14

## 四市场 × 四能力（HTTP 单元格）

| market \ capability | watch | query | screen | analyze |
|---|---|---|---|---|
| CN | PASS | PASS | SKIP | SKIP |
| US | PASS | PASS | SKIP | SKIP |
| CRYPTO | PASS | PASS | SKIP | SKIP |
| POLY | SKIP | PASS | SKIP | SKIP |

## 明细

| id | market | capability | channel | verdict | detail |
|---|---|---|---|---|---|
| G2-local-healthz | - | - | HTTP | **PASS** | status=200 items=0 |
| G2b-public-healthz | - | - | HTTP | **SKIP** | soft status=403 want=200 |
| G2-ready | - | - | HTTP | **PASS** | status=200 items=0 |
| G2-capabilities | - | - | HTTP | **PASS** | status=200 items=0 |
| M-CN-watch | CN | watch | HTTP | **PASS** | status=200 items=1 |
| M-CN-watch | CN | watch | MCP | **PASS** | status=200 items=1 |
| M-CN-watch | CN | watch | HTTP↔MCP | **PASS** | key fields match (as_of tolerance 5s) |
| M-CN-query | CN | query | HTTP | **PASS** | status=200 items=4 |
| M-CN-query | CN | query | MCP | **PASS** | status=200 items=1 |
| M-CN-query-bars | CN | query | HTTP | **PASS** | status=200 items=5 |
| M-CN-query-bars | CN | query | MCP | **PASS** | status=200 items=5 |
| M-CN-query-bars | CN | query | HTTP↔MCP | **PASS** | key fields match (as_of tolerance 5s) |
| M-CN-screen | CN | screen | HTTP | **SKIP** | N/A-phase1 status=501 |
| M-CN-analyze | CN | analyze | HTTP | **SKIP** | N/A-phase1 status=501 |
| M-US-watch | US | watch | HTTP | **PASS** | status=200 items=1 |
| M-US-watch | US | watch | MCP | **PASS** | status=200 items=1 |
| M-US-watch | US | watch | HTTP↔MCP | **PASS** | key fields match (as_of tolerance 5s) |
| M-US-query | US | query | HTTP | **PASS** | status=200 items=2 |
| M-US-query | US | query | MCP | **PASS** | status=200 items=1 |
| M-US-screen | US | screen | HTTP | **SKIP** | N/A-phase1 status=501 |
| M-US-analyze | US | analyze | HTTP | **SKIP** | N/A-phase1 status=501 |
| M-CRYPTO-watch | CRYPTO | watch | HTTP | **PASS** | status=200 items=1 |
| M-CRYPTO-watch | CRYPTO | watch | MCP | **PASS** | status=200 items=1 |
| M-CRYPTO-watch | CRYPTO | watch | HTTP↔MCP | **PASS** | key fields match (as_of tolerance 5s) |
| M-CRYPTO-query | CRYPTO | query | HTTP | **PASS** | status=200 items=2 |
| M-CRYPTO-query | CRYPTO | query | MCP | **PASS** | status=200 items=1 |
| M-CRYPTO-screen | CRYPTO | screen | HTTP | **SKIP** | N/A-phase1 status=501 |
| M-CRYPTO-analyze | CRYPTO | analyze | HTTP | **SKIP** | N/A-phase1 status=501 |
| M-POLY-watch | POLY | watch | HTTP | **SKIP** | adapter not implemented: POLY:DUMMY: POLY equity quotes unsupported; use /v1/prediction/* (phase-1: 501) |
| M-POLY-watch | POLY | watch | MCP | **SKIP** | adapter not implemented: POLY:DUMMY: POLY equity quotes unsupported; use /v1/prediction/* (phase-1: 501) |
| M-POLY-query | POLY | query | HTTP | **PASS** | status=200 items=1 |
| M-POLY-screen | POLY | screen | HTTP | **SKIP** | N/A-phase1 status=501 |
| M-POLY-analyze | POLY | analyze | HTTP | **SKIP** | N/A-phase1 status=501 |
| M-POLY-prediction | POLY | analyze | HTTP | **SKIP** | N/A-phase1 status=501 |
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
| S8 | - | analyze | HTTP | **PASS** | status=501 |
| S9 | - | watch | - | **SKIP** | phase2 |
| S14 | - | auth | - | **SKIP** | phase2 |

## Watch 重跑附录（2026-09-03 00:52 CST）

| check | status | detail |
|---|---|---|
| public/healthz | 403 | error code: 1010  |
| /healthz | 200 | {"status":"ok","service":"omnialpha","version":"0.1.0"} |
| /health/ready | 200 | {"status":"ok","postgres":true,"redis":true,"service":"omnialpha","detail":null} |
| watch CN:600519 | 200 | PASS / items=1 source=tencent last=1297.5 warn= |
| watch US:AAPL | 200 | SKIP / items=0 source=- last=None warn=US:AAPL: refresh failed: Too Many Requests. Rate limited. Try after a while. |
| watch CRYPTO:BTCUSDT | 200 | PASS / items=1 source=okx last=77290.1 warn= |
| watch POLY:DUMMY | 200 | SKIP / items=0 source=- last=None warn=POLY:DUMMY: POLY equity quotes unsupported; use /v1/prediction/* (phase-1: 501) |
| POLY query instruments | 200 | items=1 |
| POLY prediction | 501 | {"detail":"prediction not implemented in phase-1","capability":"prediction","status":"unsupported"} |
| MCP watch US:AAPL | 200 | SKIP/FAIL {'items': [], 'warnings': ['US:AAPL: refresh failed: Too Many Requests. Rate limited. Try after a while.']} |
| MCP watch CRYPTO:BTCUSDT | 200 | PASS items=1 source=okx |

## 公网 healthz 复核（2026-09-03 00:55 CST）

- `https://api.metacognix.xyz/healthz` → **200** `{"status":"ok","service":"omnialpha","version":"0.1.0"}`
- 此前本机 soft 403/CF1010 已恢复；**未**全量重跑矩阵（按 Finance 指示）。
