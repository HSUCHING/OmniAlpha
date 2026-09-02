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
│   └── prediction/       # 空位
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
git clone https://github.com/<you>/OmniAlpha.git
cd OmniAlpha
cp .env.example .env
docker compose up -d --build
```

服务默认：

| 组件 | 地址 |
|------|------|
| Facade API | `http://127.0.0.1:8700` |
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
- MCP：`$BASE/mcp`（`search_instruments` / `get_quotes` / `get_bars`）

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

---

## Docker Compose

根目录 `docker-compose.yml` 包含：

1. **postgres:16** — 标的字典 / 映射  
2. **redis:7** — 报价快照（短 TTL）  
3. **facade** — 构建本仓库镜像，监听 **8700**

说明：在部分受限主机上 facade 使用 `network_mode: host`，以便访问外部行情源与宿主机上的 Postgres/Redis 端口；详见 compose 内注释。

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f facade
```

---

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
