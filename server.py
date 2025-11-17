from __future__ import annotations

from fastmcp import FastMCP

from tools.statistics_tool import register_statistics_tools


mcp = FastMCP(name="DB-Stats-Server")


register_statistics_tools(mcp)


if __name__ == "__main__":

    mcp.run(transport="stdio")
