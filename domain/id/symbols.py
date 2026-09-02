"""Symbol ID parsing — market via prefix, never path segments."""
from __future__ import annotations

from fastapi import HTTPException

from contracts.schema import KNOWN_PREFIXES, SymbolId


def parse_symbol(raw: str) -> SymbolId:
    if not raw or not isinstance(raw, str):
        raise HTTPException(status_code=422, detail="symbol is required")
    s = raw.strip().upper()
    if ":" not in s:
        raise HTTPException(
            status_code=422,
            detail=f"invalid symbol '{raw}': expected PREFIX:CODE (e.g. CN:600519)",
        )
    prefix, _, code = s.partition(":")
    code = code.strip()
    if prefix not in KNOWN_PREFIXES:
        raise HTTPException(
            status_code=422,
            detail=f"unknown market prefix '{prefix}'; allowed: {', '.join(KNOWN_PREFIXES)}",
        )
    if not code:
        raise HTTPException(status_code=422, detail=f"empty code in symbol '{raw}'")
    # Normalize CN codes to 6 digits when numeric
    if prefix == "CN" and code.isdigit():
        code = code.zfill(6)
    return SymbolId(raw=raw.strip(), prefix=prefix, code=code)  # type: ignore[arg-type]


def parse_symbols(raw: str | list[str]) -> list[SymbolId]:
    if isinstance(raw, list):
        parts = [p for p in raw if p]
    else:
        parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        raise HTTPException(status_code=422, detail="at least one symbol required")
    return [parse_symbol(p) for p in parts]
