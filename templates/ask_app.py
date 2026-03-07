#!/usr/bin/env python3
"""Visitor question endpoint: rate-limited Claude demo with live tool use."""
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["https://jrickey.cc"], allow_methods=["POST"])

RATE_FILE  = Path("/opt/ask-app/rate.json")
MAX_PER_IP = 10
MAX_GLOBAL = 150
MAX_INPUT  = 300
MAX_TOKENS = 600

SYSTEM_PROMPT = (
    "You are an AI assistant embedded in a live cloud infrastructure portfolio site. "
    "The site runs on Azure: two Ubuntu 24.04 ARM64 VMs (app + DB) provisioned with OpenTofu, "
    "configured with Ansible. Secrets (DB password, API key) are stored in Azure Key Vault and "
    "fetched at runtime -- nothing is hardcoded. SSH key-only auth, fail2ban, unattended-upgrades, "
    "MariaDB hardening, and one MCP server (mcp-infra on the app VM) round out the stack. "
    "You have a tool to read the sentinel health log. Use it when a visitor asks about service health, "
    "recent alerts, or what the self-healing system has been doing. "
    "Keep answers concise. 3-5 lines max. Use short paragraphs or a brief list if it helps clarity. "
    "Never write a wall of text. Be direct and specific."
)

TOOLS = [
    {
        "name": "sentinel_log",
        "description": "Read the last 30 lines of /var/log/sentinel.log. Shows service health checks, alerts, auto-restarts, and config integrity results.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def _update_activity(question: str, answer: str, tools_used: list) -> None:
    try:
        path = Path("/var/www/html/activity.json")
        try:
            existing = json.loads(path.read_text()) if path.exists() else {}
            history = existing.get("calls", [])
            if not isinstance(history, list) or not history or not isinstance(history[0], dict):
                history = []
        except Exception:
            history = []
        history.insert(0, {
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "question": question[:100] + ("..." if len(question) > 100 else ""),
            "tools": tools_used if tools_used else [],
            "answer": answer,
        })
        path.write_text(json.dumps({"calls": history[:5]}))
    except Exception:
        pass


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
    data   = _load()
    now    = time.time()
    today  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    window = now - 86400

    global_count = data["global"].get(today, 0)
    if global_count >= MAX_GLOBAL:
        raise HTTPException(status_code=429, detail="Daily limit reached -- try again tomorrow.")

    hits = [t for t in data["ips"].get(ip, []) if t > window]
    if len(hits) >= MAX_PER_IP:
        raise HTTPException(status_code=429, detail=f"You've used all {MAX_PER_IP} questions for today.")

    hits.append(now)
    data["ips"][ip] = hits
    data["global"][today] = global_count + 1

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

    client   = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = [{"role": "user", "content": text}]
    tools_used = []
    answer     = ""

    for _ in range(5):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            answer = next((b.text for b in response.content if hasattr(b, "text")), "")
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tools_used.append(block.name)
                    if block.name == "sentinel_log":
                        try:
                            result = subprocess.check_output(
                                ["tail", "-n", "30", "/var/log/sentinel.log"]
                            ).decode().strip()
                        except Exception as e:
                            result = f"sentinel.log unavailable: {e}"
                    else:
                        result = "Unknown tool."
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    _update_activity(text, answer, list(dict.fromkeys(tools_used)))

    return {"answer": answer, "remaining": remaining}
