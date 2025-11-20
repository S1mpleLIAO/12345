
from __future__ import annotations

from fastmcp import FastMCP
from models.types import DailyReportFullData
from services.daily_report_service import get_full_daily_report_data
from utils.exceptions import BusinessError


def register_statistics_tools(mcp: FastMCP):
    @mcp.tool()
    def get_daily_report_data(date: str) -> DailyReportFullData:
        """
        获取指定日期（YYYY-MM-DD）的完整日报统计数据。
        
        返回数据包含三部分：
        1. stats: 总体受理量、解决率、满意率及同比变化，以及各街道/部门的考核排名(Top3/Bottom3)。
        2. top5: 诉求量排名前5的问题类型及占比。
        3. enterprise: 当日所有的企业诉求明细列表。
        """
        try:
            return get_full_daily_report_data(date)
        except BusinessError as e:
            raise e

