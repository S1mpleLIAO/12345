"""
年度分析 MCP 工具定义
"""
from __future__ import annotations
from fastmcp import FastMCP
from models.annual_analysis_types import (
    AnnualOverview,
    CategoryAnalysis,
    TimeDistribution,
    LocationAnalysis,
    ResultAnalysis,
)
from services.annual_analysis_service import (
    get_annual_overview,
    get_category_analysis,
    get_time_distribution,
    get_location_distribution,
    get_result_analysis,
)
from utils.exceptions import BusinessError


def register_annual_analysis_tools(mcp: FastMCP):
    """
    注册年度分析工具

    Args:
        mcp: FastMCP 实例
    """

    @mcp.tool()
    def get_annual_overview_tool(year: int, category: str) -> AnnualOverview:
        """
        获取年度总体基本情况

        返回指定年份和二级分类的总体数据，包括：
        - 当年和去年的总受理数及同比变化
        - 当年和去年的解决率及同比变化
        - 当年和去年的满意率及同比变化

        Args:
            year: 年份（如 2024）
            category: 二级分类名称（如"城市管理"）

        Returns:
            年度总体基本情况数据
        """
        try:
            return get_annual_overview(year, category)
        except BusinessError as e:
            raise e
        except Exception as e:
            raise BusinessError(f"获取年度总体情况失败: {str(e)}")

    @mcp.tool()
    def get_category_analysis_tool(year: int, category: str) -> CategoryAnalysis:
        """
        获取诉求分类分析

        返回指定二级分类下的三级分类分布情况，包括：
        - 每个三级分类的件数和占比
        - 每个三级分类在各街镇的分布情况

        Args:
            year: 年份
            category: 二级分类名称

        Returns:
            诉求分类分析数据
        """
        try:
            return get_category_analysis(year, category)
        except BusinessError as e:
            raise e
        except Exception as e:
            raise BusinessError(f"获取诉求分类分析失败: {str(e)}")

    @mcp.tool()
    def get_time_distribution_tool(year: int, category: str) -> TimeDistribution:
        """
        获取时间分布分析

        返回指定年份和二级分类的月度分布情况，包括：
        - 月均受理件数
        - 每个月的受理件数
        - 每个月与去年同期的对比

        Args:
            year: 年份
            category: 二级分类名称

        Returns:
            时间分布分析数据
        """
        try:
            return get_time_distribution(year, category)
        except BusinessError as e:
            raise e
        except Exception as e:
            raise BusinessError(f"获取时间分布分析失败: {str(e)}")

    @mcp.tool()
    def get_location_distribution_tool(year: int, category: str) -> LocationAnalysis:
        """
        获取点位分析（按街镇）

        返回指定二级分类在各街镇的分布情况，按件数降序排列。

        Args:
            year: 年份
            category: 二级分类名称

        Returns:
            点位分析数据
        """
        try:
            return get_location_distribution(year, category)
        except BusinessError as e:
            raise e
        except Exception as e:
            raise BusinessError(f"获取点位分析失败: {str(e)}")

    @mcp.tool()
    def get_result_analysis_tool(year: int, category: str) -> ResultAnalysis:
        """
        获取办理结果综合分析

        返回指定年份和二级分类的办理结果，包括：
        - 总体的解决率和满意率
        - 按三级分类的解决率和满意率
        - 按街镇的解决率和满意率

        Args:
            year: 年份
            category: 二级分类名称

        Returns:
            办理结果综合分析数据
        """
        try:
            return get_result_analysis(year, category)
        except BusinessError as e:
            raise e
        except Exception as e:
            raise BusinessError(f"获取办理结果分析失败: {str(e)}")
