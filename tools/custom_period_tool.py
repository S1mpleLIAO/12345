"""
自定义时间段分析 MCP 工具定义
"""
from __future__ import annotations
from fastmcp import FastMCP
from models.custom_period_types import (
    PeriodOverview,
    PeriodCategoryAnalysis,
    UnitAnalysis,
)
from services.custom_period_service import (
    get_period_overview,
    get_period_category_analysis,
    get_unit_analysis,
)
from utils.exceptions import BusinessError


def register_custom_period_tools(mcp: FastMCP):
    """
    注册自定义时间段分析工具

    Args:
        mcp: FastMCP 实例
    """

    @mcp.tool()
    def get_period_overview_tool(start_date: str, end_date: str, category: str) -> PeriodOverview:
        """
        获取时间段总体基本情况

        返回指定时间段和二级分类的总体数据，包括：
        - 总受理数
        - 解决率
        - 满意率

        Args:
            start_date: 开始时间，格式 YYYY-MM-DD HH:MM:SS
            end_date: 结束时间，格式 YYYY-MM-DD HH:MM:SS
            category: 二级分类名称（如"违法建设"）

        Returns:
            时间段总体基本情况数据
        """
        try:
            return get_period_overview(start_date, end_date, category)
        except BusinessError as e:
            raise e
        except Exception as e:
            raise BusinessError(f"获取时间段总体情况失败: {str(e)}")

    @mcp.tool()
    def get_period_category_analysis_tool(start_date: str, end_date: str, category: str) -> PeriodCategoryAnalysis:
        """
        获取诉求分类分析

        返回指定时间段和二级分类下的三级分类分布情况，包括：
        - 每个三级分类的名称
        - 每个三级分类的件数
        - 每个三级分类的占比

        Args:
            start_date: 开始时间，格式 YYYY-MM-DD HH:MM:SS
            end_date: 结束时间，格式 YYYY-MM-DD HH:MM:SS
            category: 二级分类名称

        Returns:
            诉求分类分析数据
        """
        try:
            return get_period_category_analysis(start_date, end_date, category)
        except BusinessError as e:
            raise e
        except Exception as e:
            raise BusinessError(f"获取诉求分类分析失败: {str(e)}")

    @mcp.tool()
    def get_unit_analysis_tool(start_date: str, end_date: str, category: str) -> UnitAnalysis:
        """
        获取承办单位分析

        返回指定时间段和二级分类在各承办单位的分布情况，包括：
        - 每个二级承办单位简称的件数和占比
        - 每个承办单位的所在村社区 TOP3（并列也算）

        Args:
            start_date: 开始时间，格式 YYYY-MM-DD HH:MM:SS
            end_date: 结束时间，格式 YYYY-MM-DD HH:MM:SS
            category: 二级分类名称

        Returns:
            承办单位分析数据
        """
        try:
            return get_unit_analysis(start_date, end_date, category)
        except BusinessError as e:
            raise e
        except Exception as e:
            raise BusinessError(f"获取承办单位分析失败: {str(e)}")
