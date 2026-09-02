# G1 Contracts checklist (phase1 as-built)

## Required
- [ ] `contracts/schema/models.py` defines SymbolId, Instrument, Quote, Bar, EnvelopeMixin (`as_of`,`source`,`stale`)
- [ ] `contracts/openapi.yaml` exists and documents `/v1/instruments`, `/v1/quotes`, `/v1/bars`
- [ ] `domain/id/symbols.py` accepts only `CN|US|CRYPTO|POLY` prefixes
- [ ] `apps/facade/mcp_tools.py` exposes `search_instruments`, `get_quotes`, `get_bars`
- [ ] MCP param names match HTTP (`symbols` / `symbol` / `q` / `interval` / `limit`)

## Behavioral
- [ ] Unknown prefix → HTTP 422
- [ ] Missing API key (when `DATA_FACADE_API_KEY` set) → 401
- [ ] Quote has `symbol` + `last` + envelope fields

## Enhancements (GO-WITH-FIXES if missing)
- [x] Exported JSON Schema files under `contracts/schema/`
- [x] `contracts/mcp-tools.yaml`
- [x] `contracts/id.md`
- [x] Unified Error model with `code` enum（目标契约；phase1 HTTP+detail 仍实装）
- [ ] `/v1/meta/capabilities`
