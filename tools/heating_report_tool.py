from __future__ import annotations

from fastmcp import FastMCP
from models.heatingreport_types import HeatingReportData,OffSeasonStats
from services.heating_report_service import get_full_heating_report_data,get_off_season_stats
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
    
    
    @mcp.tool()
    def get_heating_off_season_stats(year: int) -> OffSeasonStats:
        """
        获取指定年度【下一年度非供暖季】的供暖诉求统计数据。

        约定：
            - 输入 year，例如 2024
            - 实际统计区间为：2025-03-15 00:00:00 ~ 2025-11-01 00:00:00（左闭右开）

        返回:
            OffSeasonStats: 包含非供暖季的诉求总量和三级分类 Top6（数量及占比）。
        """
        try:
            return get_off_season_stats(year)
        except BusinessError as e:
            raise e
