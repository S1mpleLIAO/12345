from __future__ import annotations

from fastmcp import FastMCP
from models.heatingreport_types import HeatingReportData
from services.heating_report_service import get_full_heating_report_data
from utils.exceptions import BusinessError

def register_heating_report_tools(mcp: FastMCP):
    @mcp.tool()
    def get_heating_report_data(year: int) -> HeatingReportData:
        """
        获取指定年度供暖季的完整统计分析数据。
        
        参数:
            year (int): 供暖季起始年份 (如 2024 表示 2024-2025 年度供暖季)。
        
        返回:
            HeatingReportData: 供暖季统计分析数据，包括总体统计、月度趋势、集中供暖类诉求分析、
            高频三级分类及供热公司办理排行等信息。
        """
        try:
            return get_full_heating_report_data(year)
        except BusinessError as e:
            raise e
