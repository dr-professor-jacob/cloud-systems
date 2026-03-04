#!/usr/bin/env python3
"""MCP server — app-server tools (system metrics + nginx stats)."""
import json
import subprocess
from datetime import datetime, timezone
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


@mcp.tool()
def write_site_metrics(uptime: str, load: str, mem_used: str, mem_total: str,
                       disk_used: str, disk_total: str, disk_pct: str,
                       nginx_connections: str) -> str:
    """Write live system metrics to /var/www/html/metrics.json for the site to display."""
    data = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "uptime": uptime,
        "load": load,
        "mem_used": mem_used,
        "mem_total": mem_total,
        "disk_used": disk_used,
        "disk_total": disk_total,
        "disk_pct": disk_pct,
        "nginx_connections": nginx_connections,
    }
    path = "/var/www/html/metrics.json"
    with open(path, "w") as f:
        json.dump(data, f)
    return f"Written to {path}"


mcp.run(transport="sse")
