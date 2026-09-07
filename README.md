# OmniAlpha

**OmniAlpha** 是一套面向全市场（A 股 / 美股 / 加密 / 预测市场）的**统一市场数据 Facade**：对内按数据源适配，中间做规范化与领域能力，对外只暴露 **一套 REST API** 与 **一套 MCP**。

> 仿真优先 · 无券商密钥 · 可 Docker Compose 一键拉起  
> 公网入口示例：[`https://api.metacognix.xyz`](https://api.metacognix.xyz)

---

## 它解决什么问题

传统做法容易按「市场 × 功能 × 旧系统」切出一堆对外服务（`/ashare/quotes`、`/us/quotes`…），导致 Agent 工具爆炸、换源要改契约。

OmniAlpha 的原则：

| 原则 | 含义 |
|------|------|
| 市场是参数 | 符号前缀 `CN:` / `US:` / `CRYPTO:` / `POLY:`，不是四套 URL |
| 能力是模块 | 查 / 看 / 分析 / 选（+ Prediction 对象模型） |
| 旧系统只当供应商 | Adapter 挡在门外，对外名称不出现 vendor |
| 契约唯一 | HTTP OpenAPI 与 MCP 同一语义 |
| 网关/计费后挂 | APISIX、Lago 不进领域层 |

---

## 架构（L0–L5）

```
调用方 ── HTTP /v1 ──┐
         MCP /mcp ───┤
                     ▼
              L4 Facade (FastAPI)
              L5 FastMCP（同进程投影）
                     ▼
     L3 领域：reference / marketdata / analytics / screener / prediction
                     ▼
     L2 事实：Postgres（字典）+ Redis（快照）[+ 以后 ClickHouse]
                     ▼
     L1 Adapters：cn_watch / us / crypto / polymarket / …
                     ▼
     L0 源系统：腾讯 / HiThink / Yahoo / OKX / Polymarket / …
```

**第一期已接通：** 查询 + 看（`instruments` / `quotes` / `bars`），CN 竖切（腾讯行情）。  
**目录已预留：** `analytics` / `screener` / `prediction` 与其它 adapter 空壳。  
**完整架构再加：** APISIX（门口）、Lago（计费）、ClickHouse（时序）。

---

## 仓库结构

```
OmniAlpha/
├── apps/facade/          # L4 FastAPI + L5 FastMCP 入口
├── domain/               # 领域层（禁止 import vendor SDK）
│   ├── id/               # 统一符号解析
│   ├── reference/        # 标的字典
│   ├── marketdata/       # 报价 / K线
│   ├── analytics/        # 空位
│   ├── screener/         # 空位
│   └── prediction/       # POLY via Gamma (/v1/prediction/*)
├── adapters/             # 按源适配
│   └── cn_watch/         # 腾讯 A 股看盘（已实现）
├── contracts/            # Schema + openapi.yaml
├── docker-compose.yml    # Postgres + Redis + facade
├── deploy/compose.yml    # 同内容（部署路径副本）
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## 快速开始

```bash
git clone https://github.com/HSUCHING/OmniAlpha.git
cd OmniAlpha
cp .env.example .env
docker compose up -d --build
```

服务默认：

| 组件 | 地址 |
|------|------|
| Facade API | `http://127.0.0.1:8700` |
| Scalar API 文档 | `http://127.0.0.1:8701`（独立 nginx，只读挂载 `contracts/openapi.yaml`） |
| Postgres | `localhost:5433`（用户/库 `facade`） |
| Redis | `localhost:6379` |
| API Key | 请求头 `X-API-Key: dev-key`（可用环境变量改） |

### 冒烟

```bash
export BASE=http://127.0.0.1:8700
export KEY=dev-key

curl -sS "$BASE/healthz"
curl -sS -H "X-API-Key: $KEY" "$BASE/v1/instruments"
curl -sS -H "X-API-Key: $KEY" "$BASE/v1/quotes?symbols=CN:600519"
curl -sS -H "X-API-Key: $KEY" \
  "$BASE/v1/bars?symbol=CN:600519&interval=1d&limit=5"
```

- Swagger：`$BASE/docs`  
- MCP：`$BASE/mcp`（`search_instruments` / `get_quotes` / `get_bars` / `get_capabilities` / `search_prediction_markets` / `get_prediction_market` / `get_prediction_quote`）
- Scalar：`http://127.0.0.1:8701/`（OpenAPI 只读；试调加 `X-API-Key: dev-key`）

公网（若已配 Cloudflare Tunnel）：

```bash
export BASE=https://api.metacognix.xyz
```

---

## 对外契约（第一期）

```
GET /v1/instruments
GET /v1/quotes?symbols=CN:600519,US:AAPL
GET /v1/bars?symbol=CN:600519&interval=1d&limit=5
```

符号规范（第一天冻结）：

```
CN:600519
US:AAPL
CRYPTO:BTCUSDT
POLY:{market_id}
```

未知前缀 → **422**；缺 API Key（若已配置）→ **401**。  
规范化字段：`as_of`（UTC）、`source`、`stale`。

### Prediction（POLY）

POLY 是**预测市场**，不是股票行情。请走独立路径，**不要**用 `/v1/quotes` / `/v1/bars`。

```bash
curl -sS -H "X-API-Key: $KEY" "$BASE/v1/prediction/markets?limit=2"
curl -sS -H "X-API-Key: $KEY" "$BASE/v1/prediction/markets/{id}"
curl -sS -H "X-API-Key: $KEY" "$BASE/v1/prediction/quote?market_id={id}"
```

返回 `PredictionMarket` / `PredictionQuote`（`outcomes[].price` 为 0–1 概率）。数据源：`polymarket-gamma`。

---


## Scalar API 文档（:8701）

```bash
docker compose up -d scalar
```

| 项 | 值 |
|---|---|
| URL | `http://127.0.0.1:8701` |
| OpenAPI | `http://127.0.0.1:8701/openapi.yaml`（只读挂载 `contracts/openapi.yaml`） |
| Try-it 目标 | `http://127.0.0.1:8700` |
| API Key | 请求头 `X-API-Key: dev-key` |

**公网勿裸奔**：Scalar 仅供本地 / Compose；不要 Cloudflare Tunnel / 公网发布 `:8701`。

后续可并列挂载 MCP / GraphQL sibling 文档入口（同一契约，不另起 schema）。


## Docker Compose

根目录 `docker-compose.yml` 包含：

1. **postgres:16** — 标的字典 / 映射  
2. **redis:7** — 报价快照（短 TTL）  
3. **facade** — 构建本仓库镜像，监听 **8700**  
4. **scalar** — 独立 nginx（**:8701**），只读挂载 OpenAPI；**不在 domain、不改 capabilities**

说明：在部分受限主机上 facade 使用 `network_mode: host`，以便访问外部行情源与宿主机上的 Postgres/Redis 端口；详见 compose 内注释。

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f facade
```


## 路线图（摘要）

| 阶段 | 内容 |
|------|------|
| P1（当前） | CN 查+看竖切；Compose；MCP 三工具 |
| P2 | 美股 / 加密 / Polymarket 对齐同一 Quote/Bar 契约 |
| P3 | analytics / screener 填实 |
| P4 | APISIX 限流审计；可选 Lago 用量计费；ClickHouse |

---

## 开发约定

- `domain/` 不得直接依赖 adapter SDK  
- OpenAPI 与 MCP **禁止**各写一套字段名  
- 缺能力用 `unsupported` / 422，不要新开「无盘口专用 API」  
- 分析/选不要直打实时看盘 HTTP  

---

## License

默认私有仓库。若需开源协议，再说一声补上。

## Evaluation

See [`Eval.md`](./Eval.md) and `eval/` for architecture/implementation acceptance gates (G0–G5).

## 自动部署（deploy-* tag → webhook）

硬约束：独立服务 **:8702**；**不进** facade/domain；仅更新 **facade + scalar**；HMAC timing-safe；tag 必须 `deploy-*`；webhook **不能**选服务名。

### GitHub Secrets

| Secret | 必填 | 说明 |
|--------|------|------|
| `DEPLOY_WEBHOOK_SECRET` | 是 | 与本机 webhook 共享的 HMAC 密钥 |
| `DEPLOY_WEBHOOK_URL` | 否 | 默认 `https://deploy.metacognix.xyz/hooks/deploy` |

签名头：`X-Deploy-Signature: sha256=<hmac-sha256-hex(body)>`

### Cloudflare Tunnel

Remix 需在 Tunnel 增加：`deploy.metacognix.xyz` → `http://127.0.0.1:8702`

### 本机启动（推荐：host 进程）

Tunnel 已指向 `127.0.0.1:8702` 时，优先用 host uvicorn（免镜像构建 / apt 502）：

```bash
# .env 中设置 DEPLOY_WEBHOOK_SECRET
./deploy/scripts/run-webhook-host.sh
# 或后台：nohup ./deploy/scripts/run-webhook-host.sh >/tmp/deploy-webhook.log 2>&1 &
curl -sS http://127.0.0.1:8702/healthz
```

可选：compose 镜像（`deploy/webhook/Dockerfile` 基于 `docker:27-cli` + apk，**不再走 apt**）：

```bash
docker compose up -d --build deploy-webhook
```

### 触发

```bash
git tag deploy-YYYYMMDD-1
git push origin deploy-YYYYMMDD-1
```

Workflow 模板 `deploy/ci/deploy.yml`（需复制到 `.github/workflows/deploy.yml`；push workflow 需 GitHub `workflow` scope） 会在 push `deploy-*` tag 时向 webhook POST；接收器验签后执行 `deploy/scripts/deploy.sh <tag>`（`git fetch/checkout` + `docker compose build/up facade scalar`，**不动** PG/Redis 卷）。

