from __future__ import annotations

from fastmcp import FastMCP
from models.emergencyreport_types import (
    EmergencySummaryResult,
    EmergencyAppealResult,
)
from services.emergency_report_service import (
    get_emergency_category_stats,
    get_emergency_appeals_for_date,
)
from utils.exceptions import BusinessError


def register_emergency_report_tools(mcp: FastMCP):
    """
    在 MCP 服务中注册“紧急敏感专报”相关工具。
    """

    @mcp.tool()
    def get_emergency_category_stats_tool(date: str) -> EmergencySummaryResult:
        """
        获取某日报表日期对应统计窗口内（前一日12:00至当日12:00）：
        - 一级分类为【供暖、扬言、消防安全、供水】四类合计受理量；
        - 与上一统计期相比的增减件数及增减比例；
        - 有效件数；
        - 回访响应率、解决率、满意率等指标。
        """
        try:
            return get_emergency_category_stats(date)
        except BusinessError as e:
            raise e

    @mcp.tool()
    def get_emergency_appeals_tool(date: str) -> EmergencyAppealResult:
        """
        获取紧急敏感诉求的主要内容和处理结果：
        - 限定一级分类为【供暖、扬言、消防安全、供水】；
        - 统计窗口为前一日12:00至当日12:00。
        """
        try:
            return get_emergency_appeals_for_date(date)
        except BusinessError as e:
            raise e
