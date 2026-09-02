# 基线 vs 第二轮 diff（88e6043）

- baseline: PASS=27 FAIL=0 SKIP=18
- post_refactor: PASS=36 FAIL=0 SKIP=14
- Δ PASS: +9  FAIL: 0  SKIP: -4
- public /healthz probe (**soft**；Finance 侧曾 200，本机 CF 1010/403 不否决): `error 403`

## 四市场×能力 HTTP 单元格变化

| market | capability | baseline | post |
|---|---|---|---|
| CN | watch | PASS | PASS |
| CN | query | PASS | PASS |
| CN | screen | SKIP | SKIP |
| CN | analyze | SKIP | SKIP |
| US | watch | SKIP | PASS ← |
| US | query | PASS | PASS |
| US | screen | SKIP | SKIP |
| US | analyze | SKIP | SKIP |
| CRYPTO | watch | SKIP | PASS ← |
| CRYPTO | query | PASS | PASS |
| CRYPTO | screen | SKIP | SKIP |
| CRYPTO | analyze | SKIP | SKIP |
| POLY | watch | SKIP | SKIP |
| POLY | query | SKIP | PASS ← |
| POLY | screen | SKIP | SKIP |
| POLY | analyze | SKIP | SKIP |

## 关键变化

- **US/watch**: SKIP → PASS
- **CRYPTO/watch**: SKIP → PASS
- **POLY/query**: SKIP → PASS

## 探针 / 协议

- `/health/ready`: 基线 404 → 现网 **200**（G2-ready PASS）
- `/v1/meta/capabilities`: 基线 404 → 现网 **200**（G2-capabilities PASS）
- screen/analyze: 基线 404 SKIP → 现网 **501** SKIP（符合 N/A-phase1）
- POLY prediction `/v1/prediction/markets`: **501** SKIP
- CN/US/CRYPTO watch HTTP↔MCP: **PASS**

## 结论

第二轮相对基线：**FAIL=0**；CN/US/CRYPTO 的 watch+query 均为 PASS；screen/analyze/prediction 以 501 正确标 SKIP/N/A。公网 healthz 跑数器 soft SKIP(403)，独立探针见上。

## 公网 healthz 复核（2026-09-03 00:55 CST）

- `https://api.metacognix.xyz/healthz` → **200** `{"status":"ok","service":"omnialpha","version":"0.1.0"}`
- 此前本机 soft 403/CF1010 已恢复；**未**全量重跑矩阵（按 Finance 指示）。
