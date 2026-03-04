#!/usr/bin/env python3
"""Visitor question endpoint — rate-limited Claude demo."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["POST"])

RATE_FILE   = Path("/opt/ask-app/rate.json")
MAX_PER_IP  = 3    # per rolling 24h window
MAX_GLOBAL  = 100  # per calendar day
MAX_INPUT   = 300  # characters
MAX_TOKENS  = 250

SYSTEM_PROMPT = (
    "You are a helpful assistant on a cloud infrastructure portfolio site built by jrick. "
    "The site demonstrates Azure infrastructure (VMs, VNet, NSG, Key Vault), Ansible automation, "
    "nginx with TLS, a Model Context Protocol (MCP) server, and live Claude API integration. "
    "Answer the visitor's question in 2-3 sentences max. Be concise and friendly."
)


def _load() -> dict:
    if RATE_FILE.exists():
        try:
            return json.loads(RATE_FILE.read_text())
        except Exception:
            pass
    return {"ips": {}, "global": {}}


def _save(data: dict) -> None:
    RATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    RATE_FILE.write_text(json.dumps(data))


def _check_and_record(ip: str) -> int:
    """Check limits, record the hit, return remaining IP quota. Raises HTTPException if blocked."""
    data   = _load()
    now    = time.time()
    today  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    window = now - 86400  # 24h ago

    # Global daily cap
    global_count = data["global"].get(today, 0)
    if global_count >= MAX_GLOBAL:
        raise HTTPException(status_code=429, detail="Daily limit reached — try again tomorrow.")

    # Per-IP rolling 24h
    hits = [t for t in data["ips"].get(ip, []) if t > window]
    if len(hits) >= MAX_PER_IP:
        raise HTTPException(status_code=429, detail=f"You've used all {MAX_PER_IP} questions for today.")

    # Record
    hits.append(now)
    data["ips"][ip] = hits
    data["global"][today] = global_count + 1

    # Prune old IPs (keep last 7 days)
    cutoff = now - 7 * 86400
    data["ips"] = {k: [t for t in v if t > cutoff] for k, v in data["ips"].items() if any(t > cutoff for t in v)}

    _save(data)
    return MAX_PER_IP - len(hits)


class Question(BaseModel):
    question: str


@app.post("/ask")
async def ask(q: Question, request: Request):
    ip = request.headers.get("X-Real-IP") or request.client.host

    text = q.question.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(text) > MAX_INPUT:
        raise HTTPException(status_code=400, detail=f"Question too long (max {MAX_INPUT} characters).")

    remaining = _check_and_record(ip)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    answer = message.content[0].text

    return {"answer": answer, "remaining": remaining}
