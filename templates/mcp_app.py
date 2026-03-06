#!/usr/bin/env python3
"""MCP server — app-VM tools (sentinel health log + session activity)."""
from pathlib import Path
from datetime import datetime, timezone
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cloud-systems-app")


@mcp.tool()
def sentinel_log() -> str:
    """Return the last 30 lines of /var/log/sentinel.log — service health checks, alerts, and auto-restarts."""
    log = Path("/var/log/sentinel.log")
    if not log.exists():
        return "sentinel.log not found"
    lines = log.read_text().splitlines()
    return "\n".join(lines[-30:])


@mcp.tool()
def write_activity(question: str, answer: str, tools: list[str]) -> str:
    """Log a summary of this Claude session to /var/www/html/activity.json for the site activity feed.
    question: the user's question.
    answer: Claude's response (full or summary).
    tools: list of MCP tool names used in this session.
    """
    path = Path("/var/www/html/activity.json")
    try:
        data = json.loads(path.read_text()) if path.exists() else {"calls": []}
    except Exception:
        data = {"calls": []}

    data["calls"].insert(0, {
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": question,
        "answer": answer,
        "tools": tools,
    })
    data["calls"] = data["calls"][:20]  # keep last 20

    path.write_text(json.dumps(data, indent=2))
    return f"Activity logged ({len(data['calls'])} entries)"


mcp.run(transport="streamable-http")
