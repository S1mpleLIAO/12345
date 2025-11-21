from __future__ import annotations

from typing import List, Dict
from typing_extensions import TypedDict


class RateStats(TypedDict):
    total: int
    solved: int
    satisfied: int
    solved_rate: float
    satisfied_rate: float


class RateDiff(TypedDict):
    diff: float  # 今天 - 昨天
    trend: str  # "up" / "down" / "equal"


class StreetCount(TypedDict):
    street_name: str
    count: int


class StreetRanks(TypedDict):
    top3: List[StreetCount]
    bottom3: List[StreetCount]


class DailyStatsResult(TypedDict):
    date: str
    yesterday_date: str
    today: RateStats
    yesterday: RateStats
    streets: StreetRanks


class AppealItem(TypedDict):
    rank: int  # 序号 1~5
    appeal_type: str  # 诉求类型 / 热点问题名称
    count: int  # 数量(件)
    ratio: float  # 占比 (0~1 之间的小数，例如 0.156 表示 15.6%)


class AppealTop5Result(TypedDict):
    date: str  # 查询日期 'YYYY-MM-DD'
    total: int  # 该日期所有数据总数
    items: List[AppealItem]
    
class EnterpriseAppealItem(TypedDict):
    date: str          # 'YYYY-MM-DD'
    department: str    # 处置部门
    appeal_type: str   # 诉求类型
    content: str       # 诉求内容全文或截断


class EnterpriseAppealResult(TypedDict):
    date: str
    total: int                      # 企业诉求总数
    items: List[EnterpriseAppealItem]
    
class DailyReportFullData(TypedDict):
    stats: DailyStatsResult            # 总体情况 & 考核排名
    top5: AppealTop5Result             # 诉求热点
    enterprise: EnterpriseAppealResult # 企业诉求

class AssessmentPeriodData(TypedDict):
    start_date: str        # 考核期开始日期 YYYY-MM-DD
    end_date: str          # 考核期结束日期 YYYY-MM-DD
    total: int             # 受理量
    solved_rate: float     # 解决率（0~1 小数）
    satisfied_rate: float  # 满意率（0~1 小数）


class AssessmentResult(TypedDict):
    date: str                  # 传入的基准日期
    month_label: str           # date 所在月份，比如 "2025-03"
    this_period: AssessmentPeriodData  # 本考核期（上个月10日~当日）
    last_period: AssessmentPeriodData  # 上一考核期（再往前一个月）
    

class AssessmentRankResult(TypedDict):
    top3: List[str]      # 考核期前三部门名称
    bottom3: List[str]   # 考核期后三部门名称