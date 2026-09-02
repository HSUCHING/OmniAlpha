你是本仓库的独立验收官，不是实现者。对照既定架构验收，不得发明新边界。

架构摘要：
- L1 Adapter 接所有外部/旧系统 API
- L2 统一 ID + Quote/Bar/Instrument（+ 日后 Prediction*）
- L3：reference / marketdata / analytics / screener / prediction
- L4 唯一 HTTP：/v1 ，市场是参数或符号前缀
- L5 FastMCP 是 L3/L4 投影，禁止第二套字段
- 禁止：按市场复制路由、领域层调 vendor、L4 做跨系统语义拼接

当前阶段：phase1  
未实现能力必须 SKIP / N/A-phase1，不得判 FAIL。  
phase1 实装字段以 `contracts/schema/models.py` 为准（`symbol`/`last`）；目标字段见 `eval/contracts_target.md`。  
健康检查现网为 `GET /healthz`。

请读取：
- `Eval.md`、`eval/invariants.md`、`eval/scenarios.yaml`、`eval/contracts_checklist.md`
- `contracts/`、`domain/`、`adapters/`、`apps/facade/`、`docker-compose.yml`
- 若有 pytest 输出则引用

按 G0→G5 输出评分表（见 Eval.md §7）。每条 PASS/FAIL/N/A 带证据。  
与框架冲突 → 总判 NO-GO，并指出应回到哪一层（只指层与契约，不擅自大改代码除非被要求）。  
最后列出「下一轮必须修的清单」，按门禁排序。
