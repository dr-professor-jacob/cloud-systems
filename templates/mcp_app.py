#!/usr/bin/env python3
"""MCP server — app-server tools exposed over SSE.

Tools:
  system_info  — uptime, load averages, memory, disk
  nginx_stats  — active connections from stub_status
"""
import subprocess
from mcp import types
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import uvicorn

server = Server("cloud-systems-app")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="system_info",
            description="Return live uptime, load averages, memory, and disk usage for the app server.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="nginx_stats",
            description="Return nginx active connections and request counts from stub_status.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "system_info":
        uptime = subprocess.check_output(["uptime"]).decode().strip()
        load   = " / ".join(open("/proc/loadavg").read().split()[:3])
        mem    = subprocess.check_output(["free", "-h"]).decode().strip()
        disk   = subprocess.check_output(["df", "-h", "/"]).decode().strip()
        text = (
            f"Uptime : {uptime}\n"
            f"Load   : {load}  (1m / 5m / 15m)\n\n"
            f"Memory :\n{mem}\n\n"
            f"Disk   :\n{disk}"
        )
    elif name == "nginx_stats":
        try:
            text = subprocess.check_output(
                ["curl", "-sf", "http://127.0.0.1/nginx_status"]
            ).decode().strip()
        except Exception as e:
            text = f"stub_status unavailable: {e}"
    else:
        text = f"Unknown tool: {name}"

    return [types.TextContent(type="text", text=text)]


sse = SseServerTransport("/mcp/messages/")


async def handle_sse(scope, receive, send):
    async with sse.connect_sse(scope, receive, send) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())


async def handle_messages(scope, receive, send):
    await sse.handle_post_message(scope, receive, send)


app = Starlette(routes=[
    Route("/mcp/sse",        endpoint=handle_sse),
    Mount("/mcp/messages/",  app=handle_messages),
])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
