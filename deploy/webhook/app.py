"""Deploy webhook receiver — independent of facade/domain."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import subprocess
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

log = logging.getLogger("deploy-webhook")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SECRET = os.getenv("DEPLOY_WEBHOOK_SECRET", "").strip()
REPO_DIR = Path(os.getenv("DEPLOY_REPO_DIR", "/workspace/OmniAlpha")).resolve()
SCRIPT = Path(os.getenv("DEPLOY_SCRIPT", str(REPO_DIR / "deploy/scripts/deploy.sh"))).resolve()
TAG_RE = re.compile(r"^deploy-[A-Za-z0-9._-]+$")

app = FastAPI(title="OmniAlpha deploy webhook", version="0.1.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "deploy-webhook"}


def _verify(sig_header: str | None, body: bytes) -> None:
    if not SECRET:
        raise HTTPException(status_code=500, detail="DEPLOY_WEBHOOK_SECRET not configured")
    if not sig_header:
        raise HTTPException(status_code=401, detail="missing signature")
    token = sig_header.strip()
    if token.startswith("sha256="):
        token = token[7:]
    expected = hmac.new(SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, token):
        raise HTTPException(status_code=401, detail="invalid signature")


@app.post("/hooks/deploy")
async def hooks_deploy(
    request: Request,
    x_deploy_signature: str | None = Header(default=None, alias="X-Deploy-Signature"),
):
    body = await request.body()
    _verify(x_deploy_signature, body)
    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="invalid json") from e

    tag = (
        payload.get("tag")
        or payload.get("ref_name")
        or (str(payload.get("ref", "")).rsplit("/", 1)[-1] if payload.get("ref") else None)
    )
    if not tag or not TAG_RE.match(str(tag)):
        raise HTTPException(status_code=400, detail="tag must match deploy-*")

    if not SCRIPT.is_file():
        raise HTTPException(status_code=500, detail=f"deploy script missing: {SCRIPT}")

    cmd = ["/bin/bash", str(SCRIPT), str(tag)]
    log.info("running %s", cmd)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_DIR),
            capture_output=True,
            text=True,
            timeout=int(os.getenv("DEPLOY_TIMEOUT_SEC", "900")),
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise HTTPException(status_code=504, detail="deploy timed out") from e

    ok = proc.returncode == 0
    return JSONResponse(
        status_code=200 if ok else 500,
        content={
            "ok": ok,
            "tag": tag,
            "returncode": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-4000:],
            "stderr_tail": (proc.stderr or "")[-4000:],
        },
    )
