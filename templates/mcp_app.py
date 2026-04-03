#!/usr/bin/env python3
"""MCP server: app-VM tools (sentinel health log)."""
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cloud-systems-app")


@mcp.tool()
def sentinel_log() -> str:
    """Return the last 30 lines of /var/log/sentinel.log. Shows service health checks, alerts, and auto-restarts."""
    log = Path("/var/log/sentinel.log")
    if not log.exists():
        return "sentinel.log not found"
    lines = log.read_text().splitlines()
    return "\n".join(lines[-30:])


mcp.run(transport="streamable-http")
