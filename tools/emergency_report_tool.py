from __future__ import annotations

from fastmcp import FastMCP
from models.emergencyreport_types import (
    EmergencySummaryResult,
    EmergencyAppealResult,
    EmergencyMonthlyRateResult,
)
from services.emergency_report_service import (
    get_emergency_category_stats,
    get_emergency_appeals_for_date,
    get_emergency_month_daily_rates,
    get_emergency_month_rates, 
)
from utils.exceptions import BusinessError


def register_emergency_report_tools(mcp: FastMCP):
    """
    在 MCP 服务中注册“紧急敏感专报”相关工具。
    """

    @mcp.tool()
    def get_emergency_category_stats_tool(date: str) -> EmergencySummaryResult:
        """
        获取某日报表日期对应统计窗口内（前一日12:00至当日12:00）紧急敏感专报的四类指标：
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
        获取当日计窗口内（前一日12:00至当日12:00）紧急敏感诉求的主要内容和处理结果：
        - 限定一级分类为【供暖、扬言、消防安全、供水】；
        - 统计窗口为前一日12:00至当日12:00。
        """
        try:
            return get_emergency_appeals_for_date(date)
        except BusinessError as e:
            raise e
        
    @mcp.tool()
    def get_emergency_month_daily_rates_tool(date: str) -> EmergencyMonthlyRateResult:
        """
        获取“月考核期”内每一天的紧急敏感诉求三率情况。

        - 输入 date（YYYY-MM-DD），例如 2025-10-26；
        - 标签日期范围：上一个月19日 至 当日（两端包含）；
        - 每个标签日期 d 的统计窗口为：[d-1 日 12:00, d 日 12:00)，
          与日报和紧急敏感专报保持一致；
        - 统计对象：一级分类为【供暖、扬言、消防安全、供水】四类合并；
        - 输出：days 数组，每天包含受理总量、有效回访数、联系数、已解决数、
          满意数、基本满意数以及三率。
        """
        try:
            return get_emergency_month_daily_rates(date)
        except BusinessError as e:
            raise e
