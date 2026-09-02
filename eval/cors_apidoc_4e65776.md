# CORS / apidoc Try 冒烟（`4e65776`）

- 时间: 2026-09-03 03:52 CST
- 范围: OPTIONS/CORS + Scalar/apidoc servers（**不全量**）

## 结果摘要

| 项 | verdict | 证据 |
|---|---|---|
| Scalar try-it 指向公网 API | **PASS** | `deploy/scalar/index.html` + `:8701` / `apidoc.metacognix.xyz` 均含 `servers[0]=https://api.metacognix.xyz`（本地 8700 为 fallback） |
| 本地 CORS 精确 Origin | **PASS** | Origin=`https://apidoc.metacognix.xyz` → ACAO 回显；`evil.example` → **无** ACAO（OPTIONS 400） |
| 本地 GET + Origin | **PASS** | `/healthz`、`/v1/quotes` + X-API-Key → ACAO=`https://apidoc.metacognix.xyz` |
| 公网 OPTIONS 预检 | **PASS** | `OPTIONS https://api.metacognix.xyz/healthz` + apidoc Origin → 200，ACAO/ACAM/ACAH 正确（需正常 UA；裸爬虫易 CF 1010 **soft**） |
| 公网 healthz | **PASS**（UA） | 200 ok；无 UA 时可能 403/1010 soft |
| 契约 openapi.yaml servers | **PASS** | 含 api.metacognix.xyz + 127.0.0.1:8700 |
| 现网 `/openapi.json` servers | **NOTE** | live `servers=null`（未导出 yaml servers）；不影响 Scalar 自带 servers 配置 |

## 结论

**PASS**（CORS 精确允许 apidoc；Scalar Try 默认公网 API）。公网无 UA 探针仍 soft。未跑全量矩阵。
