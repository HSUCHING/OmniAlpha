# OmniAlpha 验收报告 · 88e6043

评测对象: `88e6043` `/workspace/OmniAlpha`（Wire multi-market ports and readiness probes）  
阶段声明: phase1  
现网: `http://127.0.0.1:8700` · `https://api.metacognix.xyz`  
验收官: OmniAlpha 审视 · 2026-09-03

## G0 不变量 8/8 PASS

| # | 结果 | 证据 |
|---|---|---|
| 1 仅 /v1 + MCP | PASS | `apps/facade/main.py` 路由均为 `/healthz` `/health/ready` `/v1/*` `/mcp`；openapi 无 `/ashare`/`/us/` |
| 2 市场为前缀/参数 | PASS | `CN/US/CRYPTO/POLY`；`domain/id` + Query `market` |
| 3 domain 禁 adapters | PASS | `rg` domain 无 `import adapters`；`ports.py` + `apps/facade/wiring.py` 组装 |
| 4 跨源映射不在 L4 | PASS | L4 调 domain；无手写跨源拼接 |
| 5 证券≠预测 | PASS | prediction 独立 `/v1/prediction/*` → 501；capabilities 不宣称 prediction；不用 Quote 冒充 |
| 6 OpenAPI↔MCP 同源 | PASS | 三主 tool 调同一 domain；`model_dump` 字段同源（prediction MCP 为 soft unsupported dict，见 FIX） |
| 7 空模块不宣称上线 | PASS | analytics/screener/prediction 目录在；capabilities analyze/screen/prediction=false |
| 8 无计费/网关进 L3 | PASS | domain/apps 无 apisix/lago/clickhouse |

## G1 契约 实装 PASS / 增强缺

实装:
- `contracts/schema/models.py` SymbolId Instrument Quote Bar EnvelopeMixin（symbol/last）PASS
- `contracts/openapi.yaml` instruments/quotes/bars PASS
- `domain/id` 四前缀；未知/无前缀 → 422 PASS
- MCP `search_instruments` `get_quotes` `get_bars` 参数同名 PASS

增强缺失（GO-WITH-FIXES）:
- 无 `contracts/schema/*.json`
- 无 `contracts/mcp-tools.yaml`
- 无 `contracts/id.md`
- 无统一 `Error.code` 枚举
- MCP prediction tool 暴露但返回 soft dict（非 HTTP 501 对等）

## G2 就绪 PASS（增强探针已补）

| 探针 | 127.0.0.1:8700 | api.metacognix.xyz |
|---|---|---|
| GET /healthz | 200 ok | 200 ok |
| GET /health/ready | 200 postgres+redis true | 200 |
| GET /v1/meta/capabilities | 200 CN/US/CRYPTO watch+query | 同左；POLY 全 false |

## G3 层间 PASS

1. parse `CN:600519` OK；`AAPL`/`FOO:1` → 422 — PASS  
2. Quote `CN:600519` source=tencent last=1297.5 as_of UTC — PASS  
3. Redis 路径存在于 `domain/marketdata/service.py` — PASS（结构）  
4. HTTP `/v1/quotes` 字段完整 — PASS  
5. MCP 调同一 `get_quotes` — PASS（静态同源）  
6. domain 无 vendor URL 硬编码；adapters 仅 wiring — PASS  

## G4 形态一致 PASS（主路径）

instruments/quotes/bars：Domain ↔ HTTP ↔ MCP 同源。  
备注：MCP prediction 与 HTTP 501 形态不完全对等 → 记增强/FIX，不否决 phase1 主路径。

## G5 场景矩阵

| ID | 结果 | 证据 |
|---|---|---|
| S1 查标的 | PASS | 200 茅台 → CN:600519 |
| S2 报价 | PASS | 200 symbol/last/as_of/source/stale |
| S3 K线 | PASS | 200 bars≥1 |
| S4 多标的 | PASS | 200 600519+000001 |
| S5 跨市场 US | PASS | 200 AAPL/MSFT 种子 |
| S6 FOO:1 | PASS | 422 |
| S7 缺 key | PASS | 401 |
| S8 未实现 | PASS | analyze/screen/prediction → 501 |
| US/CRYPTO quotes | PASS | yfinance / okx 200 |

## 评分表

```
评测对象: 88e6043 /workspace/OmniAlpha
阶段声明: phase1
G0 不变量:   8/8 PASS
G1 契约:     实装 PASS；增强 0/4（json/mcp-tools.yaml/id.md/Error.code）
G2 就绪:     facade+postgres+redis；healthz/ready/capabilities 200（本地+公网）
G3 层间:     parse/quote/HTTP/ports 静态 全 PASS
G4 形态一致: instruments/quotes/bars HTTP↔MCP↔Domain PASS；prediction MCP soft 不一致
G5 场景矩阵: S1–S8 PASS（+ US/CRYPTO quotes）
总判: GO-WITH-FIXES
必须修复: （无一票否决 FAIL；下列为增强）
  F1 导出 contracts/schema/*.json
  F2 补 contracts/mcp-tools.yaml + id.md
  F3 MCP prediction 与 HTTP 501 行为对齐（或不暴露 tool）
  F4 统一 Error.code（目标字段）
与框架冲突: 无
```

## 结论

phase1 最低线已绿；G0 跳层已解；现网就绪探针与三市场 quotes 实证通过。总判 **GO-WITH-FIXES**（契约增强与 MCP prediction 对等未闭合）。APISIX/Lago/CH/分析/选股 → N/A-phase1。
