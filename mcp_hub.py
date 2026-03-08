#!/usr/bin/env python3
"""Cloud Shell MCP hub: ops tools for monitoring and remediating the deployment.

Run from Cloud Shell:
    python3 mcp_hub.py

Connect Claude Code:
    { "mcpServers": { "cloud-ops": { "type": "streamable-http",
                                     "url": "http://localhost:8001/mcp/" } } }
"""
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cloud-ops", host="127.0.0.1", port=8001)


def _ansible(module: str, args: str) -> str:
    try:
        result = subprocess.run(
            ["ansible", "app_node", "-i", "inventory.ini", "-m", module, "-a", args],
            capture_output=True, text=True, check=True
        )
        out = result.stdout
        return out.split(">>")[-1].strip() if ">>" in out else out.strip()
    except subprocess.CalledProcessError as e:
        return f"Ansible command failed:\n--- stdout ---\n{e.stdout}\n--- stderr ---\n{e.stderr}"


def _playbook(name: str) -> str:
    try:
        result = subprocess.run(
            ["ansible-playbook", "-i", "inventory.ini", name],
            capture_output=True, text=True, check=True,
        )
        return result.stdout[-3000:]
    except subprocess.CalledProcessError as e:
        return f"Ansible playbook failed:\n--- stdout ---\n{e.stdout}\n--- stderr ---\n{e.stderr}"


@mcp.tool()
def check_health() -> str:
    """Check the status of all services on the app VM (nginx, ask-app, mcp-infra, sentinel)."""
    cmd = "for s in nginx ask-app mcp-infra sentinel.timer; do printf '%-15s' $s; systemctl is-active $s; done"
    status_raw = _ansible("shell", cmd)
    return status_raw.replace("active", "✅ ACTIVE").replace("inactive", "❌ INACTIVE").replace("activating", "⏳ ACTIVATING")


@mcp.tool()
def get_sentinel_log(lines: int = 30) -> str:
    """Read the sentinel health log from the app VM. Shows service checks, alerts, and repairs."""
    return _ansible("shell", f"tail -n {lines} /var/log/sentinel.log 2>/dev/null || echo 'Log not yet created'")


@mcp.tool()
def get_service_status(service: str) -> str:
    """Get detailed systemd status for a specific service. Options: nginx, ask-app, mcp-infra, sentinel."""
    return _ansible("shell", f"systemctl status {service} --no-pager -l 2>&1 | tail -20")


@mcp.tool()
def apply_remediation() -> str:
    """Run repair_web.yml to restore the app VM to known-good state from Ansible templates.
    Use this when sentinel logs show unresolved alerts or services are degraded."""
    return _playbook("repair_web.yml")


@mcp.tool()
def get_nginx_errors(lines: int = 20) -> str:
    """Read the nginx error log from the app VM."""
    return _ansible("shell", f"tail -n {lines} /var/log/nginx/app_error.log 2>/dev/null || tail -n {lines} /var/log/nginx/error.log 2>/dev/null")


@mcp.tool()
def restart_service(service: str) -> str:
    """Restart a specific service on the app VM. Options: nginx, ask-app, mcp-infra."""
    if service not in ["nginx", "ask-app", "mcp-infra"]:
        return "Invalid service name. Use 'nginx', 'ask-app', or 'mcp-infra'."
    return _ansible("systemd", f"name={service} state=restarted")


if __name__ == "__main__":
    print("Cloud ops MCP hub running on http://127.0.0.1:8001/mcp/")
    print("Add to .mcp.json: { \"cloud-ops\": { \"type\": \"streamable-http\", \"url\": \"http://localhost:8001/mcp/\" } }")
    mcp.run(transport="streamable-http")
