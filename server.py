from __future__ import annotations

from fastmcp import FastMCP

from tools.statistics_tool import register_statistics_tools
from tools.appeal_tool import register_appeal_tools

mcp = FastMCP(name="DB-Stats-Server")


register_statistics_tools(mcp)
register_appeal_tools(mcp)


if __name__ == "__main__":

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port="9001",
        path="/mysql",
        log_level="debug",
    )
