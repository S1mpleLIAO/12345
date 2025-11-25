
from __future__ import annotations

from fastmcp import FastMCP
from models.dailyreport_types import DailyReportFullData, StreetAssessmentResult, UnitAssessmentResult
from services.daily_report_service import get_full_daily_report_data, get_street_assessment_data, get_unit_assessment_data, get_assessment_data_for_date
from utils.exceptions import BusinessError


def register_statistics_tools(mcp: FastMCP):
    @mcp.tool()
    def get_daily_report_data(date: str) -> DailyReportFullData:
        """
        获取指定日期（YYYY-MM-DD）的完整日报统计数据。
        
        返回数据包含三部分：
        1. stats: 总体受理量、解决率、满意率及同比变化，。
        2. top5: 诉求量排名前5的问题类型及占比。
        3. enterprise: 当日所有的企业诉求明细列表。
        """
        try:
            return get_full_daily_report_data(date)
        except BusinessError as e:
            raise e
        
    @mcp.tool()
    def get_full_assessment_data_tool(date: str) -> StreetAssessmentResult:
        """
        返回当月考核期和上个月考核期的各个指标
        """
        try:
            return get_assessment_data_for_date(date)
        except BusinessError as e:
            raise e
        
        
        
    @mcp.tool()
    def get_street_assessment_data_tool(date: str) -> StreetAssessmentResult:
        """
        只能获取【乡镇街道】考核排名数据。
        返回包含：受理量、解决数、满意数、三率、综合成绩。
        """
        try:
            return get_street_assessment_data(date)
        except BusinessError as e:
            raise e

    # --- 拆分出的新工具 2 ---
    @mcp.tool()
    def get_unit_assessment_data_tool(date: str) -> UnitAssessmentResult:
        """
        只能获取【区直单位】考核排名数据。
        返回包含：受理量、解决数、满意数、三率、综合成绩。
        """
        try:
            return get_unit_assessment_data(date)
        except BusinessError as e:
            raise e

