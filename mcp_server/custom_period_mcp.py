"""
自定义时间段分析 MCP 服务器
端口：6002
路径：/custom_period_mcp
"""
from __future__ import annotations

from fastmcp import FastMCP

from tools.custom_period_tool import register_custom_period_tools

mcp = FastMCP(name="Custom-Period-Server")


# 注册自定义时间段分析工具
register_custom_period_tools(mcp)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=6002,
        path="/custom_period_mcp",
        log_level="debug",
    )
