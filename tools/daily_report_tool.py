
from __future__ import annotations

from fastmcp import FastMCP
from models.dailyreport_types import DailyReportFullData, AssessmentResult
from services.daily_report_service import get_assessment_data_for_date
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
    @mcp.tool()
    def get_assessment_data(date: str) -> AssessmentResult:
        """
        获取某日期对应的两段考核期原始指标：

        - 本考核期：上个月19日 ~ 当日
        - 上一考核期：上上个月19日 ~ 上个月同日（若不存在则该月最后一天）

        仅返回：
          - 各考核期的受理量 total
          - 解决率 solved_rate（0~1）
          - 满意率 satisfied_rate（0~1）

        对于“环比上升/下降/持平”“绝对值”“百分点”的计算，
        建议由上层 LLM 根据本工具的返回结果自行完成。
        """
        try:
            return get_assessment_data_for_date(date)
        except BusinessError as e:
            raise e

