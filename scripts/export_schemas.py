#!/usr/bin/env python3
"""Export Pydantic models to JSON Schema under contracts/schema/."""
from __future__ import annotations
import json
from pathlib import Path
from contracts.schema.models import (
    ApiError, Bar, BarList, CapabilitiesResponse, CapabilityFlags, EnvelopeMixin,
    HealthResponse, Instrument, InstrumentList, Quote, QuoteList, ReadyResponse, SymbolId,
)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "contracts" / "schema"
MODELS = {
    "symbol_id": SymbolId, "instrument": Instrument, "quote": Quote, "bar": Bar,
    "instrument_list": InstrumentList, "quote_list": QuoteList, "bar_list": BarList,
    "health": HealthResponse, "ready": ReadyResponse, "capabilities": CapabilitiesResponse,
    "capability_flags": CapabilityFlags, "envelope": EnvelopeMixin, "error": ApiError,
}
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = {"schemas": {}}
    for name, model in MODELS.items():
        schema = model.model_json_schema()
        path = OUT / f"{name}.json"
        path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        index["schemas"][name] = path.name
        print(f"wrote {path.relative_to(ROOT)}")
    (OUT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
if __name__ == "__main__":
    main()
