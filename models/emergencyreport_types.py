from __future__ import annotations

from typing import List
from typing_extensions import TypedDict


class EmergencyCategoryStats(TypedDict):
    """
    如后续需要单独展示分类明细时可以使用，目前主体统计不强制依赖。
    """
    category: str           # 一级分类名称（供暖/扬言/消防安全/供水）
    total: int              # 本期总受理量
    last_total: int         # 上期总受理量
    diff: int               # 较上一统计期增减件数（本期 - 上期）


class EmergencySummaryResult(TypedDict):
    """
    紧急敏感专报 - 汇总结果（供暖/扬言/消防安全/供水四类合并统计 + 按分类拆分）。
    """
    date: str                   # 报表日期（YYYY-MM-DD）
    period_start: str           # 本期开始时间（YYYY-MM-DD HH:MM:SS）
    period_end: str             # 本期结束时间
    last_period_start: str      # 上期开始时间
    last_period_end: str        # 上期结束时间

    # —— 总体数量及环比 ——
    total: int                  # 本期四类合计受理量
    last_total: int             # 上期四类合计受理量
    diff: int                   # 与上期相比增减件数 = total - last_total
    diff_rate: float            # 与上期相比增减比例（例如 0.182 表示 +18.2%）

    # —— 办结情况（按“办结时间”统计） ——
    finished: int               # 本期四类合计办结件数（办结时间在本期统计窗口内）

    # —— 有效回访 & 三率（按创建时间统计的有效数据）——
    valid: int                  # 有效回访数
    contact: int                # 联系数
    solved: int                 # 已解决数
    satisfied: int              # 满意数
    basic_satisfied: int        # 基本满意数

    response_rate: float        # 响应率 = contact / valid
    solved_rate: float          # 解决率 = solved / valid
    satisfied_rate: float       # 满意率 = (satisfied + 0.9 * basic_satisfied) / valid

    # —— 分类拆分 —— 
    categories: List[EmergencyCategoryStats]  # 各分类的件数及环比增减


class EmergencyAppealItem(TypedDict):
    """紧急敏感诉求明细。"""
    datetime: str           # 创建时间（精确到秒）
    department: str         # 承办单位（这里用二级承办单位简称）
    category: str           # 一级分类（供暖/扬言/消防安全/供水）
    content: str            # 主要内容
    result: str             # 办理结果/处理情况（需映射实际字段）


class EmergencyAppealResult(TypedDict):
    """紧急敏感诉求明细列表返回结果。"""
    date: str
    period_start: str
    period_end: str
    items: List[EmergencyAppealItem]
