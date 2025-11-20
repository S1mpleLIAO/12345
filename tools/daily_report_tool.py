
from __future__ import annotations

from fastmcp import FastMCP
from models.types import AppealTop5Result
from models.types import DailyStatsResult
from models.types import EnterpriseAppealResult
from services.daily_report_service import get_daily_stats_for_date, get_top5_appeal_types_for_date,get_enterprise_appeals_for_date
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
        
    @mcp.tool()
    def get_enterprise_appeals(date: str) -> EnterpriseAppealResult:
        """
        识别指定日期的企业诉求：

        输入:
          - date: 'YYYY-MM-DD'，例如 '2025-01-01'

        输出:
          - date: 日期
          - total: 企业诉求总数
          - items: 企业诉求明细列表
        """
        try:
            return get_enterprise_appeals_for_date(date)
        except BusinessError as e:
            # 业务异常（比如日期格式错误）直接抛给 FastMCP 转成 MCP 错误
            raise e

