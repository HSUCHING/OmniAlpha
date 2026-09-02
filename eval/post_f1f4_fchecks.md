# F1–F4 + Scalar 复测报告（`bb4c174`）

- 时间: 2026-09-03 03:28 CST
- BASE: `http://127.0.0.1:8700`  Scalar: `http://127.0.0.1:8701`
- 矩阵: 见 `eval/post_f1f4_report.md` → **PASS=36 FAIL=0 SKIP=14**

## 探针

| check | result |
|---|---|
| local healthz/ready/openapi | 200 / 200 / 200 |
| Scalar :8701 | **200** |
| public healthz | **403** `error code: 1010
` （矩阵侧偶发 403 仍 **soft**） |

## F1–F4

| id | 项 | verdict | 证据 |
|---|---|---|---|
| F1 | schema JSON 导出 | **PASS** | `contracts/schema/*.json` present=True |
| F2 | mcp-tools.yaml + id.md | **PASS** | mcp-tools=True id.md=True errors.md=True |
| F3 | prediction MCP↔HTTP 501 对等 | **PASS** | HTTP `/v1/prediction/*` → **501**；MCP **不暴露** prediction tool（tools=['search_instruments', 'get_quotes', 'get_bars', 'get_capabilities']） |
| F4 | Error.code 统一 | **PASS** | 401=`unauthorized` 422=`validation_error` 501=`not_implemented` |

## 场景矩阵摘要

| market\\cap | watch | query | screen | analyze |
|---|---|---|---|---|
| CN | PASS | PASS | SKIP(501) | SKIP(501) |
| US | PASS | PASS | SKIP(501) | SKIP(501) |
| CRYPTO | PASS | PASS | SKIP(501) | SKIP(501) |
| POLY | SKIP | PASS | SKIP(501) | SKIP(501)+prediction 501 |

## 结论

F1–F4：**F1 PASS / F2 PASS / F3 PASS / F4 PASS**；Scalar :8701 PASS；矩阵 FAIL=0。公网 healthz soft 口径照旧。
