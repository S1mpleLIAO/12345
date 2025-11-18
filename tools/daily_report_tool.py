
from __future__ import annotations

from fastmcp import FastMCP
from models.types import AppealTop5Result
from models.types import DailyStatsResult
from services.statistics_service import get_daily_stats_for_date
from services.appeal_service import get_top5_appeal_types_for_date
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
    
    @mcp.tool()
    def get_top5_appeal_types(date: str) -> AppealTop5Result:
        """
        统计指定日期(YYYY-MM-DD)的诉求类型 Top5：

        - 输入参数:
            date: '2025-01-01' 这样的日期字符串

        - 返回:
            {
              "date": "...",
              "total": 123,
              "items": [
                {"rank": 1, "appeal_type": "...", "count": 51, "ratio": 0.156},
                ...
              ]
            }
        """
        try:
            return get_top5_appeal_types_for_date(date)
        except BusinessError as e:
            raise e
