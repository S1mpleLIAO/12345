"""
年度分析 MCP 服务器
端口：6001
路径：/annual_analysis_mcp
"""
from __future__ import annotations

from fastmcp import FastMCP

from tools.annual_analysis_tool import register_annual_analysis_tools

mcp = FastMCP(name="Annual-Analysis-Server")


# 注册年度分析工具
register_annual_analysis_tools(mcp)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=6001,
        path="/annual_analysis_mcp",
        log_level="debug",
    )
