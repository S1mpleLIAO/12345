from __future__ import annotations

from fastmcp import FastMCP
from tools.heating_report_tool import register_heating_report_tools

# 创建 FastMCP 服务实例
mcp = FastMCP(name="HeatingReport-Server")

# 注册供暖期统计分析相关的工具方法
register_heating_report_tools(mcp)

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=9001,
        path="/heating_report_mcp",
        log_level="debug",
    )
