
from __future__ import annotations

from fastmcp import FastMCP

from models.types import DailyStatsResult
from services.statistics_service import get_daily_stats_for_date
from utils.exceptions import BusinessError


def register_statistics_tools(mcp: FastMCP):
    @mcp.tool()
    def get_daily_stats(date: str) -> DailyStatsResult:
        """
        统计指定日期（YYYY-MM-DD）与前一天的：
          - 总量
          - 解决率
          - 满意率
          - 上升/下降趋势
          - 当天处置街道 Top3 / Bottom3
        """
        try:
            return get_daily_stats_for_date(date)
        except BusinessError as e:
            raise e
