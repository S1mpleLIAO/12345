from __future__ import annotations

from fastmcp import FastMCP
from tools.emergency_report_tool import register_emergency_report_tools

mcp = FastMCP(name="EmergencyReport-Server")

# 注册紧急敏感专报相关工具
register_emergency_report_tools(mcp)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=9003,
        path="/emergency_report_mcp",
        log_level="debug",
    )
