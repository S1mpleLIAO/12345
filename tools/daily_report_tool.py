from __future__ import annotations

from fastmcp import FastMCP
from models.dailyreport_types import (
    DailyReportFullData,
    StreetAssessmentResult,
    UnitAssessmentResult,
    AssessmentResult,
)
from services.daily_report_service import (
    get_full_daily_report_data,
    get_street_assessment_data,
    get_unit_assessment_data,
    get_assessment_data_for_date,
    get_lagging_street_rank_trends,
)
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
    def get_monthly_assessment_data_tool(date: str) -> AssessmentResult:
        """
        返回当月考核期和上个月考核期的各个指标（不包含排名数据）
        """
        try:
            return get_assessment_data_for_date(date)
        except BusinessError as e:
            raise e

    @mcp.tool()
    def get_street_assessment_data_tool(date: str) -> StreetAssessmentResult:
        """
        只获取【乡镇街道】在当日的所属考核口径下的当日汇总明细（非趋势）。
        返回：受理量、解决数、满意数、三率、综合成绩及排名列表。
        不用于生成“倒数三街镇趋势表”。
        """
        try:
            return get_street_assessment_data(date)
        except BusinessError as e:
            raise e

    @mcp.tool()
    def get_unit_assessment_data_tool(date: str) -> UnitAssessmentResult:
        """
        获取【区直单位】考核排名数据。
        返回包含：受理量、解决数、满意数、三率、综合成绩。
        """
        try:
            return get_unit_assessment_data(date)
        except BusinessError as e:
            raise e

    @mcp.tool()
    def get_lagging_street_rank_trends_tool(date: str):
        """
        【专用工具】生成“落后街镇排名动态监控”所需的全部数据。
            给定 date(YYYY-MM-DD)：
            - 自动识别该日“三率综合成绩”倒数3个街镇
            - 自动计算该日所属“月考核期”（每月19日00:00起，截止到当日12:00）
            - 返回这3个街镇在该月考核期内“每日综合排名（累计口径）”趋势序列
        """
        try:
            return get_lagging_street_rank_trends(date)
        except BusinessError as e:
            raise e
