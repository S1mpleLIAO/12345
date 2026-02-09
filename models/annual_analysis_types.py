"""
年度分析数据类型定义
"""
from __future__ import annotations
from typing import TypedDict, List


# ========== 工具 1：总体基本情况 ==========
class AnnualOverview(TypedDict):
    """年度总体基本情况"""
    current_year_count: int           # 当年总受理数
    last_year_count: int              # 去年总受理数
    yoy_change: int                   # 同比变化数量
    yoy_percentage: str               # 同比变化百分比
    solve_rate: float                 # 解决率
    solve_rate_last_year: float       # 去年解决率
    solve_rate_yoy: str               # 解决率同比
    satisfaction_rate: float          # 满意率
    satisfaction_rate_last_year: float  # 去年满意率
    satisfaction_rate_yoy: str        # 满意率同比


# ========== 工具 2：诉求分类分析 ==========
class LocationDistribution(TypedDict):
    """街镇分布"""
    town: str                         # 街镇名称
    count: int                        # 件数
    percentage: float                 # 占比


class SubCategoryDetail(TypedDict):
    """三级分类详情"""
    name: str                         # 三级分类名称
    count: int                        # 件数
    percentage: float                 # 占比
    locations: List[LocationDistribution]  # 街镇分布


class CategoryAnalysis(TypedDict):
    """诉求分类分析"""
    sub_categories: List[SubCategoryDetail]


# ========== 工具 3：时间分布分析 ==========
class MonthlyData(TypedDict):
    """月度数据"""
    month: int                        # 月份（1-12）
    current_year_count: int           # 当年该月件数
    last_year_count: int              # 去年该月件数
    yoy_change: int                   # 同比变化数量
    yoy_percentage: str               # 同比变化百分比


class TimeDistribution(TypedDict):
    """时间分布分析"""
    monthly_average: float            # 月均受理件数
    monthly_data: List[MonthlyData]   # 12个月的数据


# ========== 工具 4：点位分析 ==========
class LocationItem(TypedDict):
    """街镇统计项"""
    town: str                         # 街镇名称
    count: int                        # 件数
    percentage: float                 # 占比


class LocationAnalysis(TypedDict):
    """点位分析"""
    locations: List[LocationItem]


# ========== 工具 5：办理结果分析 ==========
class OverallResult(TypedDict):
    """总体办理结果"""
    total_count: int                  # 总受理数
    solve_rate: float                 # 解决率
    satisfaction_rate: float          # 满意率


class SubCategoryResult(TypedDict):
    """三级分类办理结果"""
    name: str                         # 三级分类名称
    solve_rate: float                 # 解决率
    satisfaction_rate: float          # 满意率


class LocationResult(TypedDict):
    """街镇办理结果"""
    town: str                         # 街镇名称
    solve_rate: float                 # 解决率
    satisfaction_rate: float          # 满意率


class ResultAnalysis(TypedDict):
    """办理结果综合分析"""
    overall: OverallResult                      # 总体结果
    by_sub_category: List[SubCategoryResult]    # 按三级分类
    by_location: List[LocationResult]           # 按街镇
