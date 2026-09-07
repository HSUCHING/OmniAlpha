# 符号与 ID 规范（phase1 冻结）

市场**不是** path 段，而是符号前缀或 query `market`。

## 规范形式

```
PREFIX:CODE
```

| 前缀 | 示例 | CODE 规则（phase1） |
|---|---|---|
| `CN` | `CN:600519` | A 股；纯数字码补零到 6 位 |
| `US` | `US:AAPL` | 美股 ticker，大写 |
| `CRYPTO` | `CRYPTO:BTCUSDT` | 交易对，大写 |
| `POLY` | `POLY:{market_id}` | 预测市场 id；**prediction via `/v1/prediction/*`**（勿用 Quote/Bar 冒充概率） |

解析入口：`domain/id/symbols.py` → `SymbolId`（`contracts/schema/models.py`）。

## 行为

| 输入 | 期望 |
|---|---|
| 合法四前缀 | 200（业务允许时） |
| 未知前缀 `FOO:1` | HTTP **422** |
| 缺冒号 `AAPL` | HTTP **422** |
| 空 CODE | HTTP **422** |

## phase1 实装字段 vs 目标字段

| 概念 | phase1 实装 | 目标（`eval/contracts_target.md`） |
|---|---|---|
| 标的主键 | `symbol` | `instrument_id` |
| 最新价 | `last` | `price` |
| K 线周期 | `interval` | `timeframe` |
| K 线起点 | `open_time` | `start`（另有 `end`） |
| 包络 | `as_of` / `source` / `stale` | 同左（保留） |
| 错误 | HTTP status + `detail` | `ApiError.code` 枚举（见 `error.json`） |

目标增强（未强制）：`venue`、`native_symbol`、`timezone`、`capabilities[]`、`adjust`。

## 预测对象

证券 schema（Instrument/Quote/Bar）与 Prediction* **分离**。

- 实装：`PredictionOutcome` / `PredictionMarket` / `PredictionMarketList` / `PredictionQuote`
- HTTP：`/v1/prediction/markets`、`/v1/prediction/markets/{id}`、`/v1/prediction/quote`（events 为 markets 别名）
- MCP：`search_prediction_markets` / `get_prediction_market` / `get_prediction_quote`
- **不**经 `/v1/quotes` 或 `/v1/bars`；POLY equity watch/query 仍 unsupported
