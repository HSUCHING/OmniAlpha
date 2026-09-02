# Error 契约（F4）

## phase1 实装（现状）

| HTTP | 场景 | Body |
|---|---|---|
| 401 | 缺/错 `X-API-Key` | FastAPI `{ "detail": "..." }` |
| 422 | 非法符号 / 缺参 | `{ "detail": "..." }` |
| 501 | analyze / screen / prediction | `{ "detail": "...", ... }`（facade stub） |
| 503 | `/health/ready` 依赖失败 | `ReadyResponse` 字段 |

**无**统一 `code` 枚举。

## 目标字段（post-phase1）

见 `contracts/schema/error.json` 与 `ApiError`：

```
code ∈ not_found | unsupported | stale | invalid_id | rate_limited
message: string
market?: CN|US|CRYPTO|POLY
capability?: watch|query|analyze|screen|prediction
```

映射建议（实现官对齐时）：

| 现状 | 目标 code |
|---|---|
| 未知前缀 / 缺冒号 | `invalid_id` |
| 标的不存在 | `not_found` |
| prediction/analyze/screen stub | `unsupported` |
| 过期仍返回 | `stale`（可伴随 `stale: true`） |
| 上游限流 | `rate_limited` |

phase1 **不因**未切换到 `ApiError` 而 NO-GO；属 GO-WITH-FIXES 增强项 F4。
