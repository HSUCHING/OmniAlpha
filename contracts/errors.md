# Error 契约（F4）

## phase1 实装（现状）

| HTTP | 场景 | Body |
|---|---|---|
| 401 | 缺/错 `X-API-Key` | FastAPI `{ "detail": "..." }` |
| 422 | 非法符号 / 缺参 | `{ "detail": "..." }`；明显 ID 问题 → `ApiError(code=invalid_id)` |
| 501 | analyze / screen / prediction | `ApiError(code=unsupported)` |
| 404 | 资源不存在 | `ApiError(code=not_found)` |
| 503 | `/health/ready` 依赖失败 | `ReadyResponse` 字段 |

**锁定**目标五码：`not_found|unsupported|stale|invalid_id|rate_limited`。勿另起 `unauthorized` / `validation_error` / `not_implemented` 等冲突枚举（对齐 `be48ceb`）。

## 目标字段

见 `contracts/schema/error.json` 与 `ApiError`。
