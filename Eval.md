# OmniAlpha · Eval Engineering

> 用途：人和 AI **反复验收**架构与实现是否符合既定框架。  
> 核心：**先验不变量 → 契约完整性 → 进程就绪 → 层间连通 → 多形态调用一致 → 场景矩阵**。  
> 原则：未实现能力标 `N/A-phase1` / `SKIP`，**不得判 FAIL**；一旦宣称实现，必须过对应门禁。

本文是定稿评估机制；可机读细则在 `eval/`。

---

## 0. 对本草案的修订说明（相对初稿）

初稿结构 **采用**：G0→G5、评分表、`eval_once` 提示词、phase 裁剪，均保留。

对照当前仓库（commit 实现）做了这些 **对齐/完善**：

| 点 | 初稿 | 修订 |
|---|---|---|
| 健康检查 | `/health` | 现网为 **`/healthz`**；`/health/ready`、`/v1/meta/capabilities` 列为 **应补探针**（未有则 G2 GO-WITH-FIXES，不直接 NO-GO） |
| Schema 载体 | 多个 `*.json` | phase1 **以 `contracts/schema/models.py`（Pydantic）+ `contracts/openapi.yaml` 为真相**；JSON 文件为可选导出，缺 JSON 不 NO-GO |
| 字段名 | `instrument_id` / `price` | phase1 实装为 **`symbol` / `last`**；G1 验「实装字段集」。目标字段（instrument_id…）放 `eval/contracts_target.md`，升级时再升格 |
| MCP 契约文件 | `mcp-tools.yaml` | 可从 `apps/facade/mcp_tools.py` 推导；缺独立 yaml → GO-WITH-FIXES |
| 错误码形态 | 统一 Error schema | phase1 多为 HTTP 422/401 + `detail`；G1 要求「行为正确」，完整 `error.json` 为增强项 |
| 跳层检测 | domain 禁 httpx 旧 URL | 补充：`apps/facade` 与 `domain` **不得** import 具体 vendor 客户端；adapter 可 httpx |
| 公网 | 未写 | 可选 G2b：`https://api.metacognix.xyz/healthz`（运维，失败不否决本地 GO） |

---

## 1. 门禁总览

| 门禁 | 验什么 | 失败意味着 |
|---|---|---|
| **G0** 不变量 | 架构有没有被推翻 | 按市场裂 API、跳层、两套语义 |
| **G1** 契约 | 协议/数据结构是否完整（相对阶段） | schema 缺核心字段、ID 不统一、OpenAPI≠MCP |
| **G2** 就绪 | Docker/服务是否起来 | 容器、健康检查、依赖 |
| **G3** 层间 | 各层是否对接成功 | L1 没吐 L2、L4 直连 vendor |
| **G4** 调用 | Domain / HTTP / MCP 三种形态 | 同输入不同业务字段 |
| **G5** 场景 | 市场 × 能力 × 异常 | 只测快乐路径 |

AI 每次验收必须按 **G0→G5** 出报告。**G0 不过 → 后面分数作废，总判 NO-GO。**

---

## 2. G0 架构不变量（每次必跑）

逐条 `PASS / FAIL / N/A` + 证据路径。条文见 `eval/invariants.md`。

摘要：

1. 对外只有 L4 `/v1` 与 L5 MCP；无 `/ashare/`、`/us/`、`/系统A/`。  
2. 市场是参数或符号前缀 `CN:` / `US:` / `CRYPTO:` / `POLY:`。  
3. Vendor 只在 `adapters/`；`domain/` 不 import vendor SDK。  
4. 跨源语义/ID 映射只在 L2，不在 L4 手写拼接。  
5. 证券对象与预测对象分开；禁止用 `Bar` 冒充 prediction。  
6. OpenAPI 与 MCP 同源（同一套 models / 导出 schema）。  
7. `analytics/`、`screener/`、`prediction/` 目录在；空实现不得注册为已上线能力。  
8. 无 APISIX/Lago/CH 写进 L3；计费/网关不进领域层。  

任一 FAIL → 评语写「与既定框架冲突」，并指出应回到哪一层。

---

## 3. G1 协议与数据结构

### 3.1 阶段真相源（phase1）

必须存在且可读：

```text
contracts/schema/models.py      # Instrument Quote Bar SymbolId EnvelopeMixin
contracts/openapi.yaml
apps/facade/mcp_tools.py        # tool 名与参数
domain/id/symbols.py            # 四前缀解析
```

增强（缺则 GO-WITH-FIXES，非 NO-GO）：

```text
contracts/schema/*.json         # 从 Pydantic 导出
contracts/mcp-tools.yaml
contracts/id.md
eval/contracts_target.md        # 目标字段（instrument_id 等）
```

### 3.2 phase1 实装必填字段

**Instrument**：`symbol`, `name`, `market`, `as_of`, `source`, `stale`  
**Quote**：`symbol`, `last`, `as_of`, `source`, `stale`  
**Bar**：`symbol`, `interval`, `open_time`, `open/high/low/close`, `as_of`, `source`  
**SymbolId**：合法四前缀；未知 → HTTP **422**

目标增强字段（不阻塞 phase1 GO）：`capabilities[]`, `timezone`, `adjust`, 统一 `Error.code` 枚举等 → 见 `eval/contracts_target.md`。

### 3.3 对齐检查

- 未知前缀 → 422  
- REST 与 MCP 参数同名（`symbols` / `symbol`，禁止一边 `tickers`）  
- `unsupported` 未实现前：未暴露的路由不得 500 伪装  
- 缺能力不得用「空数组成功」冒充已实现筛选/分析  

---

## 4. G2 服务就绪

| 服务 | 健康条件 |
|---|---|
| facade | `GET /healthz` 200；`/docs` 或 openapi 可拉 |
| postgres | ready；`instruments`（或等价）表/种子存在 |
| redis | PING；可缓存 quote |

AI 核对：compose 与文档一致；`DATABASE_URL` / `REDIS_URL` / `DATA_FACADE_API_KEY`；启动依赖。

**应补（增强）：**

```text
GET /health/ready           → PG+Redis 连上
GET /v1/meta/capabilities   → 声明 implemented 的 market×capability
```

无这两项 → G2 记 GO-WITH-FIXES，场景矩阵用 `eval/scenarios.yaml` 的 `phase` 字段裁剪。

可选 G2b：`curl -sS https://api.metacognix.xyz/healthz`。

---

## 5. G3 层间对接

禁止用「容器 up」代替「层接通」。

```text
L1     adapter 夹具 → 输出符合 Quote/Bar schema
L1→L2  jsonschema / pydantic 校验
L2     Redis/PG 写读不丢 as_of/source
L3     mock repo，不打真 vendor
L3→L4  TestClient / curl /v1
L3→L5  MCP tool 与 L3 一致
静态   facade+domain 不得 import adapters.* 的 http 客户端实现细节越层
```

phase1 最小用例：

1. `parse("CN:600519")` OK；无前缀 `AAPL` → 422  
2. 腾讯或夹具 → `Quote.symbol==CN:600519` 且 `as_of` 为 UTC  
3. Redis 缓存后 `get_quotes` 同 `as_of`（允许短 TTL 内）  
4. `GET /v1/quotes?symbols=CN:600519` 与领域结果关键字段一致  
5. MCP `get_quotes` 同上  
6. 静态：`domain/` 无 vendor URL 硬编码  

未实现模块：`@pytest.mark.skip(reason="phase2")`；AI 须区分 skip 与 fail。

---

## 6. G4 / G5 调用形态与场景

### 6.1 三形态一致

| 形态 | 怎么调 |
|---|---|
| A Domain | 领域函数 |
| B HTTP | `GET /v1/...` + `X-API-Key` |
| C MCP | `search_instruments` / `get_quotes` / `get_bars` |

业务字段一致；`as_of` / `stale` / `source` 不得在 MCP 丢失。

### 6.2 场景（详见 `eval/scenarios.yaml`）

**phase1 最低交付：** S1–S4 + S6–S8 + A/B/C 一致。

| ID | 内容 | phase1 |
|---|---|---|
| S1 | 查标的 | 必过 |
| S2 | 报价 | 必过 |
| S3 | K 线 | 必过 |
| S4 | 多标的 quotes | 必过 |
| S5 | 跨市场 | 有种子则过，否则 SKIP |
| S6 | `FOO:1` → 422 | 必过 |
| S7 | 不存在标的 | 行为明确即可 |
| S8 | 未实现能力 | 无路由 / 501 / unsupported，非 500 |
| S9–S15 | stale/鉴权/限流/多源… | 按实现声明 |

---

## 7. 评分表（AI 固定输出）

```text
评测对象: <commit / 目录>
阶段声明: phase1 | phase2 | full
G0 不变量:   xx/8 PASS
G1 契约:     xx/yy PASS（区分实装 vs 目标）
G2 就绪:     服务列表 + healthz
G3 层间:     用例列表
G4 形态一致: HTTP↔MCP↔Domain
G5 场景矩阵: 附表
总判: GO | GO-WITH-FIXES | NO-GO
必须修复: 仅 FAIL 编号
与框架冲突: 有/无（有则 NO-GO）
```

一票否决：G0 冲突；G1 缺核心实装 schema/ID；G2 facade/依赖不起；G3 主链路未通；G4 HTTP↔MCP 不一致。  
仅缺 phase2 / 增强探针 → 可为 GO 或 GO-WITH-FIXES。

---

## 8. 仓库评估资产

```text
Eval.md                          # 本文
eval/
  invariants.md
  contracts_checklist.md
  contracts_target.md
  scenarios.yaml
  rubrics.md
  fixtures/
    vendor_cn_quote.json
    canonical_quote.json
  prompts/
    eval_once.md
tests/                           # 逐步补齐自动化
  ...
```

---

## 9. 执行节奏

1. 改分层/契约 → G0 + G1（静态）  
2. 改 adapter/领域 → G1 + G3  
3. Compose up → G2 + G3 + G4  
4. 宣称某能力完成 → 打开 scenarios 对应行，不得 SKIP  
5. 发版 → 全部门禁；parity 必绿  

循环：实现 → `eval/prompts/eval_once.md` → 只修 FAIL → 再评。

---

## 10. phase1 GO 最低线

- G0 全过（空模块目录允许）  
- G1：models 中 Instrument/Quote/Bar + openapi + 三 MCP tool 对齐  
- G2：facade + postgres + redis；`/healthz` 200  
- G3：至少一条 L1→L2→L3→L4 与 L5（真源或夹具）  
- G4：instruments/quotes/bars 三形态一致  
- G5：S1–S4、S6–S8  

APISIX / Lago / CH / 分析 / 选 / WS → N/A-phase1。
