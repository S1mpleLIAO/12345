from __future__ import annotations

from fastmcp import FastMCP

from tools.daily_report_tool import register_statistics_tools

mcp = FastMCP(name="Report-Server")


register_statistics_tools(mcp)


if __name__ == "__main__":

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=9001,
        path="/daily_report_mcp",
        log_level="debug",
    )
