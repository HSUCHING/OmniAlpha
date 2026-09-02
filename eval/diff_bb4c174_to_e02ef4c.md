# 验收对象升级差分：`bb4c174` → `e02ef4c`

- 时间: 2026-09-03 03:29 CST
- 验收 HEAD（Finance）: **`e02ef4c`**
- 相对 bb4c174: +`b22b7ee`（F4 ErrorBody 强制）+ **`e02ef4c`（Contract ApiError only，去掉 ErrorBody extras；保留 F3 + Scalar :8701）**
- 测试报告 commit: `e88f8f7`（初测挂 bb4c174 标签，现改挂 e02ef4c）

## 差分结论（相对已跑 bb4c174 轮）

| 项 | bb4c174 轮（已测） | e02ef4c 期望 | 现网 :8700 实测 | verdict |
|---|---|---|---|---|
| 场景矩阵 | PASS=36 FAIL=0 | 不变 | CN/US/CRYPTO watch PASS；screen/analyze/prediction 501 SKIP | **PASS**（功能无回归） |
| F3 prediction MCP↔HTTP | MCP 不暴露 pred tools；HTTP 501 | 同左 | tools=`search_instruments/get_quotes/get_bars/get_capabilities`；HTTP prediction **501** | **PASS** |
| Scalar :8701 | 200 | 200 | **200** | **PASS** |
| F4 Error.code | unauthorized/validation_error/not_implemented + detail | ApiError: `not_found\|unsupported\|stale\|invalid_id\|rate_limited`；无 detail | 仍返回旧体：`code=unauthorized/validation_error/not_implemented` **含 detail** | **GAP：现网未跑到 e02ef4c 镜像** |
| 公网 healthz | soft | soft | 偶发 403/CF1010 | **soft** |

## 关键 GAP

现网 facade 进程/镜像 **尚未切换到 `e02ef4c` 的 ApiError 形态**（仓库 `contracts/schema/error.json` / `models.ApiError` 已无 `detail`，且 501 应为 `unsupported`）。请 @实现 rebuild 后我再点一次 F4 冒烟；**不否决**本轮场景矩阵与 F1–F3/Scalar。

## 结论

- 以 **`e02ef4c`** 为验收对象：功能场景 + F1/F2/F3 + Scalar = **PASS**（与 bb4c174 轮一致，无功能回归）。
- F4 契约差分需 **rebuild 现网后再验**；此前 bb4c174 轮 F4 PASS 对应旧 ErrorBody 枚举，不能直接算作 e02ef4c F4 闭合。
