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
    AppealItem,
    AppealTop5Result,
    EnterpriseAppealItem,
    EnterpriseAppealResult,
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

def get_top5_appeal_types_for_date(date_str: str) -> AppealTop5Result:
    """
    给定日期（YYYY-MM-DD），统计该日“诉求类型”出现次数 Top5 及占比。
      序号 / 诉求类型 / 数量(件) / 占比
    """
    # 1. 规范化日期
    try:
        d = parse_date(date_str)
    except ValueError:
        raise BusinessError("日期格式必须为 YYYY-MM-DD，例如 '2025-01-01'")

    date_str = format_date(d)

    table = get_table_name()
    conn = get_connection()
    try:
        # 2. 查当天总数
        sql_total = f"""
            SELECT COUNT(*) AS total_count
            FROM {table}
            WHERE `日期` = %s;
        """
        with conn.cursor() as cur:
            cur.execute(sql_total, (date_str,))
            row = cur.fetchone() or {}
        total = int(row.get("total_count") or 0)

        # 没有数据，直接返回空列表
        if total == 0:
            return {
                "date": date_str,
                "total": 0,
                "items": [],
            }

        # 3. 按诉求类型分组，取前 5 个
        sql_group = f"""
            SELECT
                `诉求类型` AS type_name,
                COUNT(*) AS cnt
            FROM {table}
            WHERE `日期` = %s
            GROUP BY `诉求类型`
            ORDER BY cnt DESC
            LIMIT 5;
        """
        with conn.cursor() as cur:
            cur.execute(sql_group, (date_str,))
            rows = cur.fetchall() or []

        items: List[AppealItem] = []
        rank = 1
        for r in rows:
            count = int(r["cnt"])
            ratio = count / total if total else 0.0
            items.append(
                {
                    "rank": rank,
                    "appeal_type": r["type_name"],
                    "count": count,
                    "ratio": ratio,
                }
            )
            rank += 1

        return {
            "date": date_str,
            "total": total,
            "items": items,
        }

    finally:
        release_connection(conn)
        
def get_enterprise_appeals_for_date(date_str: str) -> EnterpriseAppealResult:
    """
    识别某一天的“企业诉求”：
      - 统计企业诉求总数
      - 列出每一条企业诉求的：处置部门、诉求类型、工单内容

    企业诉求判定规则（默认版，可以后细化）：
      - 诉求类型包含“企业” OR
      - 工单内容包含“企业”
    """
    # 1. 校验并规范化日期
    try:
        d = parse_date(date_str)
    except ValueError:
        raise BusinessError("日期格式必须为 YYYY-MM-DD，例如 '2025-01-01'")

    date_str = format_date(d)

    table = get_table_name()
    conn = get_connection()
    try:
        # 2. 查询符合条件的企业诉求列表
        sql = f"""
            SELECT
                `日期`        AS dt,
                `处置部门`    AS dept,
                `诉求类型`    AS appeal_type,
                `工单内容`    AS content
            FROM {table}
            WHERE `日期` = %s
              AND (
                    `诉求类型` LIKE %s
                 OR `工单内容` LIKE %s
              )
            ORDER BY `日期` ASC, `处置部门` ASC;
        """
        like_pattern = "%企业%"

        with conn.cursor() as cur:
            cur.execute(sql, (date_str, like_pattern, like_pattern))
            rows = cur.fetchall() or []

        items: List[EnterpriseAppealItem] = []
        for r in rows:
            items.append(
                {
                    "date": r["dt"],
                    "department": r["dept"],
                    "appeal_type": r.get("appeal_type") or "",
                    "content": r.get("content") or "",
                }
            )

        return {
            "date": date_str,
            "total": len(items),
            "items": items,
        }

    finally:
        release_connection(conn)