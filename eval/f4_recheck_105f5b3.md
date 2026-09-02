# F4 补测（rebuild tip `105f5b3`）

- 时间: 2026-09-03 03:31 CST
- BASE: `http://127.0.0.1:8700`
- 总判 F4: **PASS**

## 用例

| case | status | want | code | want_code | verdict | note |
|---|---|---|---|---|---|---|
| pred_501 | 501 | 501 | unsupported | unsupported | **PASS** | keys=['capability', 'code', 'market', 'message'] code=unsupported msg=prediction not implemented in phase-1 |
| analyze_501 | 501 | 501 | unsupported | unsupported | **PASS** | keys=['capability', 'code', 'market', 'message'] code=unsupported msg=analytics not implemented in phase-1 |
| screen_501 | 501 | 501 | unsupported | unsupported | **PASS** | keys=['capability', 'code', 'market', 'message'] code=unsupported msg=screener not implemented in phase-1 |
| foo_422 | 422 | 422 | invalid_id | invalid_id | **PASS** | keys=['capability', 'code', 'market', 'message'] code=invalid_id msg=unknown market prefix 'FOO'; allowed: CN, US, CRYPTO, POLY |
| nokey_401 | 401 | 401 | None | None | **PASS** | keys=['detail'] code=None (401 dual-track detail OK) |

## Live OpenAPI error schema

```
no ApiError/ErrorBody schema in live openapi
```

## 相对 GAP 闭合

- 旧 ErrorBody 码（unauthorized/validation_error/not_implemented）**已消失**
- 501 → `unsupported`；422 FOO:1 → `invalid_id`
- 401 缺 Key 按双轨 `detail`（实现口径）接受，不阻断 F4
