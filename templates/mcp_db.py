#!/usr/bin/env python3
"""MCP server — DB tools (localhost:8001, SSH tunnel for remote access)."""
import os
import pymysql
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cloud-systems-db")

DB_NAME = os.environ.get("MCP_DB_NAME", "appdb")


def _connect():
    return pymysql.connect(
        unix_socket="/var/run/mysqld/mysqld.sock",
        user="root",
        db=DB_NAME,
    )


@mcp.tool()
def db_status() -> str:
    """Return active connection count and per-table row/size stats."""
    try:
        conn = _connect()
        with conn.cursor() as cur:
            cur.execute("SHOW STATUS LIKE 'Threads_connected'")
            threads = cur.fetchone()
            cur.execute(
                "SELECT table_name, table_rows, ROUND(data_length/1024, 1) "
                "FROM information_schema.tables WHERE table_schema = %s",
                (DB_NAME,),
            )
            tables = cur.fetchall()
        conn.close()
        out = f"Active connections: {threads[1]}\n\nTables in {DB_NAME}:\n"
        out += "\n".join(f"  {t[0]:30s} ~{t[1] or 0} rows  {t[2] or 0} KB" for t in tables) or "  (none)"
    except Exception as e:
        out = f"DB error: {e}"
    return out


@mcp.tool()
def db_version() -> str:
    """Return MariaDB version and server uptime."""
    try:
        conn = _connect()
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            version = cur.fetchone()[0]
            cur.execute("SHOW STATUS LIKE 'Uptime'")
            s = int(cur.fetchone()[1])
        conn.close()
        h, r = divmod(s, 3600)
        m, s = divmod(r, 60)
        return f"MariaDB : {version}\nUptime  : {h}h {m}m {s}s"
    except Exception as e:
        return f"DB error: {e}"


mcp.run(transport="sse", port=8001)
