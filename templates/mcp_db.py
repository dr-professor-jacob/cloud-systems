#!/usr/bin/env python3
"""MCP server — database tools exposed over SSE (localhost only).

Tools:
  db_status  — connection count and per-table row/size stats
  db_version — MariaDB version and uptime

Connect via SSH tunnel:
  ssh -L 8001:127.0.0.1:8001 jrick@<app-ip> -J jrick@<app-ip>  (from outside)
  Or directly on the DB host.
"""
import os
import pymysql
from mcp import types
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import uvicorn

server = Server("cloud-systems-db")

DB_NAME = os.environ.get("MCP_DB_NAME", "appdb")


def _connect():
    return pymysql.connect(
        unix_socket="/var/run/mysqld/mysqld.sock",
        user="root",
        db=DB_NAME,
    )


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="db_status",
            description="Return active connection count and per-table row/size stats.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="db_version",
            description="Return MariaDB version string and server uptime.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        conn = _connect()
        with conn.cursor() as cur:
            if name == "db_status":
                cur.execute("SHOW STATUS LIKE 'Threads_connected'")
                threads = cur.fetchone()
                cur.execute(
                    "SELECT table_name, table_rows, ROUND(data_length/1024, 1) "
                    "FROM information_schema.tables WHERE table_schema = %s",
                    (DB_NAME,),
                )
                tables = cur.fetchall()
                out = f"Active connections : {threads[1]}\n\nTables in {DB_NAME}:\n"
                if tables:
                    for t in tables:
                        out += f"  {t[0]:30s}  ~{t[1] or 0} rows  {t[2] or 0} KB\n"
                else:
                    out += "  (no tables yet)\n"
                text = out

            elif name == "db_version":
                cur.execute("SELECT VERSION()")
                version = cur.fetchone()[0]
                cur.execute("SHOW STATUS LIKE 'Uptime'")
                uptime_s = int(cur.fetchone()[1])
                h, rem = divmod(uptime_s, 3600)
                m, s   = divmod(rem, 60)
                text = f"MariaDB version : {version}\nServer uptime   : {h}h {m}m {s}s"

            else:
                text = f"Unknown tool: {name}"
        conn.close()
    except Exception as e:
        text = f"DB error: {e}"

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
    uvicorn.run(app, host="127.0.0.1", port=8001)
