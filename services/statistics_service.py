from __future__ import annotations

from typing import Any, Dict, List

from db.connection import get_connection, release_connection
from db.table import get_table_name
from utils.dates import parse_date, format_date, get_yesterday
from utils.exceptions import BusinessError
from models.types import (
    RateStats,
    RateDiff,
    StreetCount,
    StreetRanks,
    DailyStatsResult,
)


def _calc_rates(row: Dict[str, Any]) -> RateStats:
    total = int(row.get("total_count") or 0)
    solved = int(row.get("solved_count") or 0)
    satisfied = int(row.get("satisfied_count") or 0)

    return {
        "total": total,
        "solved": solved,
        "satisfied": satisfied,
        "solved_rate": solved / total if total else 0.0,
        "satisfied_rate": satisfied / total if total else 0.0,
    }


def _calc_diff(today: float, yesterday: float) -> RateDiff:
    diff = today - yesterday
    if diff > 0:
        trend = "上升"
    elif diff < 0:
        trend = "下降"
    else:
        trend = "equal"
    return {"diff": diff, "trend": trend}


def _query_stats_for_date(conn, date_str: str) -> RateStats:
    table = get_table_name()
    sql = f"""
        SELECT
            COUNT(*) AS total_count,
            SUM(CASE WHEN `是否解决` = '是' THEN 1 ELSE 0 END) AS solved_count,
            SUM(CASE WHEN `是否满意` = '是' THEN 1 ELSE 0 END) AS satisfied_count
        FROM {table}
        WHERE `日期` = %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (date_str,))
        row = cur.fetchone() or {}

    return _calc_rates(row)


def _query_street_ranks_for_date(conn, date_str: str) -> StreetRanks:
    """
    查询指定日期“处置部门”的出现次数 Top3 / Bottom3。
    字段：
      - `日期`
      - `处置部门`
    """
    table = get_table_name()
    sql = f"""
        SELECT
            `处置部门` AS dept_name,
            COUNT(*) AS cnt
        FROM {table}
        WHERE `日期` = %s
        GROUP BY `处置部门`
        ORDER BY cnt DESC;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (date_str,))
        rows = cur.fetchall() or []

    all_list: List[StreetCount] = [
        {"street_name": r["dept_name"], "count": int(r["cnt"])} for r in rows
    ]

    top3 = all_list[:3]
    bottom3 = all_list[-3:] if len(all_list) >= 3 else all_list

    return {"top3": top3, "bottom3": bottom3}


def get_daily_stats_for_date(date_str: str) -> DailyStatsResult:
    """
    对外主函数：
      输入：date_str = 'YYYY-MM-DD'（如 '2025-01-01'）
      输出：当天统计 + 昨天统计 + 对比 + 处置部门排名
    """
    try:
        d = parse_date(date_str)
    except ValueError:
        raise BusinessError("日期格式必须为 YYYY-MM-DD，例如 '2025-01-01'")

    yesterday_date = get_yesterday(d)

    today_str = format_date(d)
    yest_str = format_date(yesterday_date)

    conn = get_connection()
    try:
        today_stats = _query_stats_for_date(conn, today_str)
        yesterday_stats = _query_stats_for_date(conn, yest_str)
        streets = _query_street_ranks_for_date(conn, today_str)

        return {
            "date": today_str,
            "yesterday_date": yest_str,
            "today": today_stats,
            "yesterday": yesterday_stats,
            "streets": streets,
        }
    finally:
        release_connection(conn)
