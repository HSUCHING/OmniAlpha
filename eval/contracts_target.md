# Target schema (post-phase1) — do not FAIL phase1 for these gaps

Aspirational normalized fields (from architecture doc). Migrate carefully; keep OpenAPI+MCP in lockstep.

**Instrument:** `instrument_id`, `asset_class`, `market`, `venue`, `native_symbol`, `currency`, `timezone`, `capabilities[]`  
**Quote:** `instrument_id`, `price`|bid/ask, `as_of`, `source`, `stale`, `market`  
**Bar:** `instrument_id`, `timeframe`, OHLC V, `start`/`end` UTC, `adjust`, `source`  
**Error:** `code` in `not_found|unsupported|stale|invalid_id|rate_limited`, `message`, optional `market`/`capability`  
  → 契约载体：`contracts/schema/error.json`、`contracts/errors.md`、`ApiError`（目标；phase1 仍用 HTTP+detail）  
**Prediction*:** `event_id`/`market_id`/`outcome_id`, `as_of`, `source`; links via `related_instruments[]`

Phase1 mapping: `symbol` ≈ `instrument_id`, `last` ≈ `price`, `interval` ≈ `timeframe`, `open_time` ≈ `start`.

Exported JSON (phase1 as-built): `contracts/schema/*.json` + `index.json`.
