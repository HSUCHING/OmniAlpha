# G0 Invariants

For each item: PASS / FAIL / N/A + evidence (path or command).

1. Public surface is only `/v1/*` and MCP (`/mcp`); no market-copied paths (`/ashare/`, `/us/quotes`, vendor names in paths).
2. Market is a symbol prefix or query param (`CN|US|CRYPTO|POLY`), not a microservice per market.
3. Vendor SDKs / raw upstream HTTP live under `adapters/` only; `domain/` must not import vendor clients.
4. Cross-source identity/relationship mapping belongs in L2 (DB/dict), not handwritten joins in L4 handlers.
5. Equity schemas and prediction schemas are separate; do not reuse `Bar` as Polymarket probability.
6. OpenAPI and MCP share the same field names from `contracts/schema` (models or exported JSON).
7. `domain/analytics`, `domain/screener`, `domain/prediction` directories exist; empty modules must not be advertised as implemented in capabilities.
8. No billing/gateway logic inside L3; APISIX/Lago/ClickHouse absence is OK in phase1.
