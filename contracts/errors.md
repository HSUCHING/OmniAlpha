# Error 契约（F4）

## phase1 实装

Facade handlers return unified `ErrorBody` with a `code` field:

| HTTP | 场景 | `code` |
|---|---|---|
| 401 | 缺/错 `X-API-Key` | `unauthorized` |
| 422 | 非法符号 / 缺参 / 校验失败 | `validation_error` |
| 501 | analyze / screen / prediction | `not_implemented` |
| 503 | `/health/ready` 依赖失败 | `dependency_unavailable` |

Schema: `contracts/schema/error.json` · models: `ErrorCode` + `ErrorBody`（`ApiError` 别名）。

```
code ∈ not_found | unsupported | stale | invalid_id | rate_limited
     | unauthorized | validation_error | not_implemented
     | dependency_unavailable | upstream_error | internal_error
message: string
detail?: any
market?: CN|US|CRYPTO|POLY
capability?: watch|query|analyze|screen|prediction
```
