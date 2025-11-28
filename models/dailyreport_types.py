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

class DeptAssessmentRecord(TypedDict):
    """
    单个部门考核期记录结构，供街道/区直单位使用。

    对应表头：
    | 序号 | 承办单位 | 受理量 | 办结量 | 有效回访 | 联系数 | 解决数 | 满意数 | 基本满意 |
    | 响应率(%) | 解决率(%) | 满意率(%) | 综合成绩 |
    """

    department: str              # 承办单位
    total: int                   # 受理量（全部）
    closed: int                  # 办结量（按办结时间统计）
    valid: int                   # 有效回访（是否有效回访=是）
    contact: int                 # 联系数（有效回访 AND 是否联系=是）
    solved: int                  # 解决数（有效回访 AND 是否解决=是）
    satisfied: int               # 满意数（有效回访 AND 是否满意=满意）
    basic_satisfied: int         # 基本满意数（有效回访 AND 是否满意=基本满意）

    response_rate: float         # 响应率 = 联系数 / 有效回访
    solved_rate: float           # 解决率 = 解决数 / 有效回访
    satisfied_rate: float        # 满意率 = (满意 + 0.9×基本满意) / 有效回访

    score: float                 # 综合成绩： (响应率*0.1 + 满意率*0.4 + 解决率*0.5) * 100

# 新增：街道考核结果专用结构
class StreetAssessmentResult(TypedDict):
    date: str
    period_start: str
    period_end: str
    # 这里的 records 必须严格等于 16 条
    records: List[DeptAssessmentRecord]
    summary: DeptAssessmentRecord

# 新增：区直单位考核结果专用结构
class UnitAssessmentResult(TypedDict):
    date: str
    period_start: str
    period_end: str
    # 这里的 records 必须严格等于 33 条
    records: List[DeptAssessmentRecord]
    summary: DeptAssessmentRecord

class AssessmentRankResult(TypedDict):
    street_records: List[DeptAssessmentRecord] # 街道排名（严格16个）
    unit_records: List[DeptAssessmentRecord]   # 委办局排名（严格33个）

class AssessmentResult(TypedDict):
    date: str
    month_label: str
    this_period: AssessmentPeriodData
    last_period: AssessmentPeriodData