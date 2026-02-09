"""
自定义时间段分析数据类型定义
"""
from __future__ import annotations
from typing import TypedDict, List


# ========== 工具 1：总体基本情况 ==========
class PeriodOverview(TypedDict):
    """时间段总体基本情况"""
    total_count: int                  # 总受理数
    solve_rate: float                 # 解决率
    satisfaction_rate: float          # 满意率


# ========== 工具 2：诉求分类分析 ==========
class SubCategoryItem(TypedDict):
    """三级分类统计项"""
    name: str                         # 三级分类名称
    count: int                        # 件数
    percentage: float                 # 占比


class PeriodCategoryAnalysis(TypedDict):
    """诉求分类分析"""
    sub_categories: List[SubCategoryItem]


# ========== 工具 3：承办单位分析 ==========
class CommunityItem(TypedDict):
    """村社区统计项"""
    name: str                         # 村社区名称
    count: int                        # 件数


class UnitItem(TypedDict):
    """承办单位统计项"""
    name: str                         # 二级承办单位简称
    count: int                        # 件数
    percentage: float                 # 占比
    top_communities: List[CommunityItem]  # 所在村社区 TOP3


class UnitAnalysis(TypedDict):
    """承办单位分析"""
    units: List[UnitItem]
