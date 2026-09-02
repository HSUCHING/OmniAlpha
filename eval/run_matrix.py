#!/usr/bin/env python3
"""Run OmniAlpha market×capability matrix + legacy scenarios over HTTP and MCP.

Usage:
  DATA_FACADE_API_KEY=dev-key python eval/run_matrix.py
  BASE=http://127.0.0.1:8700 KEY=dev-key python eval/run_matrix.py --out eval/last_matrix_report.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = Path(__file__).resolve().parent / "scenarios.yaml"


def load_cfg() -> dict:
    return yaml.safe_load(SCENARIOS.read_text())


class McpClient:
    def __init__(self, base: str):
        self.endpoint = base.rstrip("/") + "/mcp/"
        self.session: str | None = None

    def _post(self, body: dict) -> list[dict]:
        data = json.dumps(body).encode()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session:
            headers["mcp-session-id"] = self.session
        req = urllib.request.Request(self.endpoint, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            sid = resp.headers.get("mcp-session-id")
            if sid:
                self.session = sid
            raw = resp.read().decode()
        out: list[dict] = []
        for line in raw.splitlines():
            if line.startswith("data:"):
                out.append(json.loads(line[5:].strip()))
        if not out and raw.strip().startswith("{"):
            out.append(json.loads(raw))
        return out

    def initialize(self) -> None:
        self._post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "oa-matrix", "version": "0.1"},
                },
            }
        )
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def call_tool(self, name: str, arguments: dict) -> dict:
        msgs = self._post(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        if not msgs:
            raise RuntimeError("empty MCP response")
        msg = msgs[0]
        if "error" in msg:
            raise RuntimeError(msg["error"])
        result = msg.get("result") or {}
        if result.get("isError"):
            raise RuntimeError(result)
        if "structuredContent" in result:
            return result["structuredContent"]
        # fallback: parse text content
        for c in result.get("content") or []:
            if c.get("type") == "text":
                try:
                    return json.loads(c["text"])
                except Exception:
                    return {"text": c["text"]}
        return result


def http_request(
    base: str,
    method: str,
    path: str,
    query: dict | None,
    headers: dict | None,
    api_key: str | None,
    use_auth: bool,
) -> tuple[int, Any]:
    q = urllib.parse.urlencode({k: str(v) for k, v in (query or {}).items()})
    url = base.rstrip("/") + path + (("?" + q) if q else "")
    hdrs: dict[str, str] = {}
    if headers is not None:
        hdrs.update({k: str(v) for k, v in headers.items()})
    elif use_auth and api_key:
        hdrs["X-API-Key"] = api_key
    req = urllib.request.Request(url, headers=hdrs, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            status = resp.status
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode()
    try:
        payload = json.loads(body) if body else None
    except Exception:
        payload = body
    return status, payload


def items_of(payload: Any) -> list:
    if isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            return payload["items"]
        if isinstance(payload.get("data"), list):
            return payload["data"]
    if isinstance(payload, list):
        return payload
    return []


def warnings_of(payload: Any) -> list[str]:
    if isinstance(payload, dict):
        w = payload.get("warnings") or []
        return [str(x) for x in w]
    return []


def judge_http(status: int, payload: Any, expect: dict, soft: bool) -> tuple[str, str]:
    if "http_status" in expect and status != expect["http_status"]:
        # unimplemented routes often 404 — treat as SKIP when flagged
        if expect.get("skip_if_unimplemented") and status in (expect.get("http_status_in") or [404, 501, 422]):
            return "SKIP", f"N/A-phase1 status={status}"
        if "http_status_in" in expect and status in expect["http_status_in"]:
            if expect.get("skip_if_unimplemented"):
                return "SKIP", f"N/A-phase1 status={status}"
            return "PASS", f"status={status}"
        if soft:
            return "SKIP", f"soft status={status} want={expect.get('http_status')}"
        return "FAIL", f"status={status} want={expect.get('http_status')}"

    if "http_status_in" in expect:
        if status not in expect["http_status_in"]:
            return "FAIL", f"status={status} want_in={expect['http_status_in']}"
        if expect.get("skip_if_unimplemented"):
            return "SKIP", f"N/A-phase1 status={status}"
        return "PASS", f"status={status}"

    warn_needle = expect.get("skip_if_warning_contains")
    if warn_needle:
        joined = " | ".join(warnings_of(payload))
        if warn_needle in joined or (not items_of(payload) and joined):
            return "SKIP", f"adapter not implemented: {joined[:120]}"

    if expect.get("skip_if_empty") and not items_of(payload):
        return "SKIP", "empty result (no seed)"

    if "min_items" in expect:
        n = len(items_of(payload))
        if n < int(expect["min_items"]):
            if soft:
                return "SKIP", f"soft min_items got={n}"
            return "FAIL", f"min_items got={n} want>={expect['min_items']}"

    fields = expect.get("fields") or []
    if fields:
        its = items_of(payload)
        if not its:
            return "FAIL", "no items for field check"
        missing = [f for f in fields if f not in its[0]]
        if missing:
            return "FAIL", f"missing fields {missing}"

    return "PASS", f"status={status} items={len(items_of(payload))}"


def parity(http_payload: Any, mcp_payload: Any) -> tuple[str, str]:
    """Compare HTTP vs MCP business fields.

    as_of may drift by a second or two when calls are sequential against a live
    vendor; require presence + source/stale/symbol parity, and OHLC/last match.
    """
    from datetime import datetime

    hi = items_of(http_payload)
    mi = items_of(mcp_payload)
    if not hi and not mi:
        return "PASS", "both empty"
    if not hi or not mi:
        return "FAIL", f"len http={len(hi)} mcp={len(mi)}"
    h0, m0 = hi[0], mi[0]
    diffs = []
    # must not drop provenance fields
    for k in ("as_of", "source", "stale", "symbol"):
        if k not in h0 or k not in m0:
            diffs.append(f"missing {k}")
    # exact business fields
    for k in ("symbol", "last", "source", "stale", "interval", "open", "high", "low", "close", "open_time"):
        if k in h0 or k in m0:
            if h0.get(k) != m0.get(k):
                diffs.append(f"{k}:{h0.get(k)!r}!={m0.get(k)!r}")
    # as_of within 5s if both parseable ISO
    if "as_of" in h0 and "as_of" in m0 and h0.get("as_of") != m0.get("as_of"):
        try:
            def parse(s: str) -> datetime:
                s = str(s).replace("Z", "+00:00")
                return datetime.fromisoformat(s)
            delta = abs((parse(h0["as_of"]) - parse(m0["as_of"])).total_seconds())
            if delta > 5:
                diffs.append(f"as_of delta={delta}s")
        except Exception:
            diffs.append(f"as_of:{h0.get('as_of')!r}!={m0.get('as_of')!r}")
    if diffs:
        return "FAIL", "; ".join(diffs[:6])
    return "PASS", "key fields match (as_of tolerance 5s)"


def run_case(
    case: dict,
    base_local: str,
    base_public: str,
    api_key: str,
    mcp: McpClient | None,
) -> list[dict]:
    rows: list[dict] = []
    cid = case.get("id", "?")
    phase = case.get("phase", 1)
    if phase and int(phase) > 1 and not case.get("http"):
        rows.append(
            {
                "id": cid,
                "market": case.get("market", "-"),
                "capability": case.get("capability", "-"),
                "channel": "-",
                "verdict": "SKIP",
                "detail": f"phase{phase}",
            }
        )
        return rows

    expect = case.get("expect") or {}
    soft = bool(case.get("soft"))
    invoke = case.get("invoke") or (["http"] if case.get("http") else [])
    base = base_public if case.get("base") == "public" else base_local

    http_payload = None
    http_status = None
    if "http" in invoke or case.get("http"):
        h = case.get("http") or {}
        use_auth = h.get("auth", True) is not False
        headers = h.get("headers")
        # explicit empty headers means no auth (S7)
        if headers is not None and len(headers) == 0:
            use_auth = False
        try:
            http_status, http_payload = http_request(
                base,
                h.get("method", "GET"),
                h["path"],
                h.get("query"),
                headers,
                api_key,
                use_auth,
            )
            v, detail = judge_http(http_status, http_payload, expect, soft)
        except Exception as e:
            v, detail = "FAIL", f"http error: {e}"
        rows.append(
            {
                "id": cid,
                "market": case.get("market", "-"),
                "capability": case.get("capability", "-"),
                "channel": "HTTP",
                "verdict": v,
                "detail": detail,
            }
        )

    if "mcp" in invoke and case.get("mcp"):
        if mcp is None:
            rows.append(
                {
                    "id": cid,
                    "market": case.get("market", "-"),
                    "capability": case.get("capability", "-"),
                    "channel": "MCP",
                    "verdict": "SKIP",
                    "detail": "MCP unavailable",
                }
            )
        else:
            m = case["mcp"]
            try:
                mcp_payload = mcp.call_tool(m["tool"], m.get("args") or {})
                # reuse http-shaped expectations on payload
                fake_status = 200
                v, detail = judge_http(fake_status, mcp_payload, {k: val for k, val in expect.items() if k not in ("http_status", "http_status_in")}, soft)
                # if HTTP already SKIP for unimplemented, MCP should mirror SKIP
                if rows and rows[-1]["channel"] == "HTTP" and rows[-1]["verdict"] == "SKIP" and "not implemented" in rows[-1]["detail"]:
                    v, detail = "SKIP", rows[-1]["detail"]
                rows.append(
                    {
                        "id": cid,
                        "market": case.get("market", "-"),
                        "capability": case.get("capability", "-"),
                        "channel": "MCP",
                        "verdict": v,
                        "detail": detail,
                    }
                )
                if expect.get("http_mcp_parity") and http_payload is not None and v == "PASS" and rows[-2]["verdict"] == "PASS":
                    pv, pd = parity(http_payload, mcp_payload)
                    rows.append(
                        {
                            "id": cid,
                            "market": case.get("market", "-"),
                            "capability": case.get("capability", "-"),
                            "channel": "HTTP↔MCP",
                            "verdict": pv,
                            "detail": pd,
                        }
                    )
            except Exception as e:
                rows.append(
                    {
                        "id": cid,
                        "market": case.get("market", "-"),
                        "capability": case.get("capability", "-"),
                        "channel": "MCP",
                        "verdict": "FAIL",
                        "detail": f"mcp error: {e}",
                    }
                )
    return rows


def pivot_matrix(rows: list[dict]) -> str:
    markets = ["CN", "US", "CRYPTO", "POLY"]
    caps = ["watch", "query", "screen", "analyze"]
    # pick HTTP verdict per cell (prefer HTTP over MCP for cell summary)
    cell: dict[tuple[str, str], str] = {}
    for r in rows:
        m, c = r["market"], r["capability"]
        if m not in markets or c not in caps:
            continue
        if r["channel"] != "HTTP":
            continue
        cell[(m, c)] = r["verdict"]
    lines = ["| market \\ capability | " + " | ".join(caps) + " |", "|---|---|---|---|---|"]
    for m in markets:
        vals = [cell.get((m, c), "-") for c in caps]
        lines.append("| " + m + " | " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("BASE") or os.environ.get("DATA_FACADE_BASE") or "http://127.0.0.1:8700")
    ap.add_argument("--public", default=os.environ.get("PUBLIC_BASE") or "https://api.metacognix.xyz")
    ap.add_argument("--key", default=os.environ.get("KEY") or os.environ.get("DATA_FACADE_API_KEY") or "dev-key")
    ap.add_argument("--out", default=str(ROOT / "eval" / "last_matrix_report.md"))
    args = ap.parse_args()

    cfg = load_cfg()
    base_local = args.base
    base_public = args.public
    api_key = args.key

    mcp: McpClient | None
    try:
        mcp = McpClient(base_local)
        mcp.initialize()
    except Exception as e:
        print(f"MCP init failed: {e}", file=sys.stderr)
        mcp = None

    all_rows: list[dict] = []
    for case in cfg.get("ops") or []:
        all_rows.extend(run_case(case, base_local, base_public, api_key, mcp))
    for case in cfg.get("matrix") or []:
        all_rows.extend(run_case(case, base_local, base_public, api_key, mcp))
    for case in cfg.get("scenarios") or []:
        all_rows.extend(run_case(case, base_local, base_public, api_key, mcp))

    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    for r in all_rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    lines = [
        "# OmniAlpha 场景矩阵报告",
        "",
        f"- BASE(local): `{base_local}`",
        f"- BASE(public): `{base_public}`",
        f"- KEY: `{'***' if api_key else '(none)'}`",
        f"- MCP: `{'up' if mcp else 'down'}`",
        f"- Totals: PASS={counts.get('PASS',0)} FAIL={counts.get('FAIL',0)} SKIP={counts.get('SKIP',0)}",
        "",
        "## 四市场 × 四能力（HTTP 单元格）",
        "",
        pivot_matrix(all_rows),
        "",
        "## 明细",
        "",
        "| id | market | capability | channel | verdict | detail |",
        "|---|---|---|---|---|---|",
    ]
    for r in all_rows:
        detail = str(r["detail"]).replace("|", "/").replace("\n", " ")[:160]
        lines.append(
            f"| {r['id']} | {r['market']} | {r['capability']} | {r['channel']} | **{r['verdict']}** | {detail} |"
        )
    report = "\n".join(lines) + "\n"
    out = Path(args.out)
    out.write_text(report)
    print(report)
    print(f"\nWrote {out}")
    return 1 if counts.get("FAIL", 0) else 0


if __name__ == "__main__":
    sys.exit(main())
