from __future__ import annotations

from typing import List
from typing_extensions import TypedDict

class HeatingStats(TypedDict):
    """供暖季总体统计数据，包括诉求总量和三率（解决率、满意率、响应率）。"""
    start_date: str        # 供暖季开始日期 YYYY-MM-DD
    end_date: str          # 供暖季结束日期 YYYY-MM-DD
    total: int             # 供暖季诉求总量
    solved: int            # 已解决诉求数量（有效回访且标记为已解决）
    satisfied: int         # 满意诉求数量（有效回访且评价为满意）
    solved_rate: float     # 解决率 = 已解决数 / 有效回访数
    satisfied_rate: float  # 满意率 = (满意数 + 0.9 × 基本满意数) / 有效回访数
    response_rate: float   # 响应率 = 联系数 / 有效回访数

class MonthlyStatItem(TypedDict):
    """供暖季单月统计条目。"""
    month: str            # 月份，格式 YYYY-MM
    total: int            # 当月诉求受理总量
    solved_rate: float    # 当月解决率
    satisfied_rate: float # 当月满意率

class CentralHeatingStats(TypedDict):
    """集中供暖相关诉求统计。"""
    total: int            # 集中供暖类诉求总量
    ratio: float          # 集中供暖类诉求占供暖诉求总量的比值 (0~1)
    solved_rate: float    # 集中供暖类诉求的解决率
    satisfied_rate: float # 集中供暖类诉求的满意率

class CategoryItem(TypedDict):
    """高频三级分类统计条目。"""
    rank: int            # 排名序号 (1开始)
    category_name: str   # 三级分类名称
    count: int           # 诉求数量
    ratio: float         # 占供暖诉求总量的比率 (0~1)

class CompanyItem(TypedDict):
    """供热公司办理诉求排名条目。"""
    rank: int            # 排名序号 (1开始)
    company_name: str    # 二级承办单位简称（供热公司名称）
    count: int           # 诉求数量
    ratio: float         # 占供暖诉求总量的比率 (0~1)

class HeatingReportData(TypedDict):
    """供暖季统计分析数据结构。"""
    stats: HeatingStats                    # 总体供暖诉求统计
    monthly: List[MonthlyStatItem]         # 按月统计列表
    central_heating: CentralHeatingStats   # 集中供暖类诉求统计
    categories: List[CategoryItem]         # 高频三级分类列表
    companies: List[CompanyItem]           # 供热公司办理排行列表
