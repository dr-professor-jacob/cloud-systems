#!/usr/bin/env python3
"""MCP server — app-server tools (system metrics + nginx stats)."""
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cloud-systems-app")


@mcp.tool()
def system_info() -> str:
    """Return live uptime, load averages, memory, and disk usage for the app server."""
    uptime = subprocess.check_output(["uptime"]).decode().strip()
    load   = " / ".join(open("/proc/loadavg").read().split()[:3])
    mem    = subprocess.check_output(["free", "-h"]).decode().strip()
    disk   = subprocess.check_output(["df", "-h", "/"]).decode().strip()
    return f"Uptime : {uptime}\nLoad   : {load}  (1m/5m/15m)\n\nMemory:\n{mem}\n\nDisk:\n{disk}"


@mcp.tool()
def nginx_stats() -> str:
    """Return nginx active connections from stub_status."""
    try:
        return subprocess.check_output(
            ["curl", "-sf", "http://127.0.0.1/nginx_status"]
        ).decode().strip()
    except Exception as e:
        return f"stub_status unavailable: {e}"


mcp.run(transport="sse")
