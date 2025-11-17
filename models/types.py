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
    diff: float         # 今天 - 昨天
    trend: str          # "up" / "down" / "equal"


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
    compare: Dict[str, RateDiff]
    streets: StreetRanks
