#!/usr/bin/env python3
"""Visitor question endpoint -- rate-limited Claude demo with live tool use."""
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
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["POST"])

RATE_FILE  = Path("/opt/ask-app/rate.json")
MAX_PER_IP = 30
MAX_GLOBAL = 1000
MAX_INPUT  = 300
MAX_TOKENS = 600

SYSTEM_PROMPT = (
    "You are an AI assistant embedded in a live cloud infrastructure portfolio site. "
    "The site runs on Azure: two Ubuntu 24.04 ARM64 VMs (app + DB) provisioned with OpenTofu, "
    "configured with Ansible. Secrets (DB password, API key) are stored in Azure Key Vault and "
    "fetched at runtime -- nothing is hardcoded. SSH key-only auth, fail2ban, unattended-upgrades, "
    "MariaDB hardening, and two MCP servers (one per VM) round out the stack. "
    "You have tools to query live server state. Use them whenever a visitor asks about "
    "server health, load, memory, disk, or nginx. "
    "Keep answers concise — 3-5 lines max. Use short paragraphs or a brief list if it helps clarity. "
    "Never write a wall of text. Be direct and specific."
)

TOOLS = [
    {
        "name": "system_info",
        "description": "Get live uptime, load averages (1m/5m/15m), memory, and disk usage for this server.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "nginx_stats",
        "description": "Get nginx active connections and request counts from the stub_status endpoint.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "sentinel_log",
        "description": "Read the last 30 lines of /var/log/sentinel.log — shows service health checks, alerts, auto-restarts, and config integrity results.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def _run_system_info() -> str:
    uptime = subprocess.check_output(["uptime"]).decode().strip()
    load   = " / ".join(open("/proc/loadavg").read().split()[:3])
    mem    = subprocess.check_output(["free", "-h"]).decode().strip()
    disk   = subprocess.check_output(["df", "-h", "/"]).decode().strip()
    return f"Uptime : {uptime}\nLoad   : {load}  (1m/5m/15m)\n\nMemory:\n{mem}\n\nDisk:\n{disk}"


def _run_nginx_stats() -> str:
    try:
        return subprocess.check_output(
            ["curl", "-sf", "http://127.0.0.1/nginx_status"]
        ).decode().strip()
    except Exception as e:
        return f"stub_status unavailable: {e}"


def _update_metrics(system_data: str, nginx_data: str) -> None:
    try:
        lines = system_data.split("\n")
        uptime_val = next((l.replace("Uptime :", "").strip() for l in lines if "Uptime" in l), "")
        load_val   = next((l.replace("Load   :", "").strip() for l in lines if "Load" in l), "")
        load_1m    = load_val.split()[0].rstrip(",") if load_val else ""

        mem_line  = next((l for l in lines if "Mem:" in l), "")
        mem_parts = mem_line.split()
        mem_total = mem_parts[1] if len(mem_parts) > 1 else ""
        mem_used  = mem_parts[2] if len(mem_parts) > 2 else ""

        disk_lines = [l for l in lines if "/" in l and "Filesystem" not in l and "tmpfs" not in l]
        disk_parts = disk_lines[-1].split() if disk_lines else []
        disk_total = disk_parts[1] if len(disk_parts) > 1 else ""
        disk_used  = disk_parts[2] if len(disk_parts) > 2 else ""
        disk_pct   = disk_parts[4] if len(disk_parts) > 4 else ""

        nginx_conns = ""
        for l in nginx_data.split("\n"):
            if "Active connections" in l:
                nginx_conns = l.split(":")[1].strip()
                break

        data = {
            "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "uptime": uptime_val,
            "load": load_1m,
            "mem_used": mem_used,
            "mem_total": mem_total,
            "disk_used": disk_used,
            "disk_total": disk_total,
            "disk_pct": disk_pct,
            "nginx_connections": nginx_conns,
        }
        Path("/var/www/html/metrics.json").write_text(json.dumps(data))
    except Exception:
        pass


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


@app.on_event("startup")
async def startup():
    try:
        _update_metrics(_run_system_info(), _run_nginx_stats())
    except Exception:
        pass


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
    tools_used  = []
    system_data = ""
    nginx_data  = ""
    answer      = ""

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
                    if block.name == "system_info":
                        result = _run_system_info()
                        system_data = result
                    elif block.name == "nginx_stats":
                        result = _run_nginx_stats()
                        nginx_data = result
                    elif block.name == "sentinel_log":
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

    if system_data or nginx_data:
        _update_metrics(system_data, nginx_data)
    _update_activity(text, answer, list(dict.fromkeys(tools_used)))

    return {"answer": answer, "remaining": remaining}
