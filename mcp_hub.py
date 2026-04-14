#!/usr/bin/env python3
"""Local MCP hub server — development entry point.
Runs on port 8001 via streamable-http transport.
Tools are available to Claude Code in this workspace.
"""
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cloud-hub", host="127.0.0.1", port=8001)


@mcp.tool()
def sentinel_log() -> str:
    """Return the last 30 lines of the local sentinel log (if present)."""
    candidates = [
        Path("/var/log/sentinel.log"),
        Path("sentinel.log"),
    ]
    for p in candidates:
        if p.exists():
            lines = p.read_text().splitlines()
            return "\n".join(lines[-30:])
    return "sentinel.log not found locally — connect to app VM for live log."


@mcp.tool()
def project_status() -> str:
    """Return a brief git status summary for the cloud project."""
    import subprocess
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent),
    )
    if result.returncode != 0:
        return f"git error: {result.stderr.strip()}"
    output = result.stdout.strip()
    return output if output else "Working tree clean."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
