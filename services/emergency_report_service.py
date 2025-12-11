from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Dict, List

from db.connection import get_connection, release_connection
from db.table import get_table_name
from utils.dates import parse_date, format_date, get_yesterday
from utils.exceptions import BusinessError
from models.emergencyreport_types import (
    EmergencySummaryResult,
    EmergencyAppealItem,
    EmergencyAppealResult,
    EmergencyCategoryStats,
)

# 关注的紧急敏感一级分类
EMERGENCY_CATEGORIES: List[str] = ["供暖", "扬言", "消防安全", "供水"]


def _get_noon_range_for_date(date_str: str) -> tuple[datetime, datetime]:
    """
    把报表日期（例如 '2025-05-01'）映射为：
    [2025-04-30 12:00:00, 2025-05-01 12:00:00)
    用于紧急敏感专报的统计窗口。
    """
    d = parse_date(date_str)
    end_dt = datetime.combine(d, time(12, 0, 0))
    start_dt = end_dt - timedelta(days=1)
    return start_dt, end_dt


def _query_category_raw_stats(conn, start_dt: datetime, end_dt: datetime) -> Dict[str, Dict[str, int]]:
    """
    在指定时间窗口内，按一级分类统计基础计数。
    返回 {category: {...raw_counts...}}。
    统计口径：按“创建时间”落在 [start_dt, end_dt) 内。
    """
    table = get_table_name()

    placeholders = ", ".join(["%s"] * len(EMERGENCY_CATEGORIES))
    sql = f"""
        SELECT
            `一级分类` AS category,
            COUNT(*) AS total_count,
            SUM(CASE WHEN `是否有效回访` = '是' THEN 1 ELSE 0 END) AS valid_count,
            SUM(CASE WHEN `是否有效回访` = '是' AND `是否联系` = '是' THEN 1 ELSE 0 END) AS contact_count,
            SUM(CASE WHEN `是否有效回访` = '是' AND `是否解决` = '是' THEN 1 ELSE 0 END) AS solved_count,
            SUM(CASE WHEN `是否有效回访` = '是' AND `是否满意` = '满意' THEN 1 ELSE 0 END) AS satisfied_count,
            SUM(CASE WHEN `是否有效回访` = '是' AND `是否满意` = '基本满意' THEN 1 ELSE 0 END) AS basic_satisfied_count
        FROM {table}
        WHERE `创建时间` >= %s
          AND `创建时间` < %s
          AND `一级分类` IN ({placeholders})
        GROUP BY `一级分类`;
    """

    params: List = [start_dt, end_dt] + EMERGENCY_CATEGORIES
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall() or []

    result: Dict[str, Dict[str, int]] = {}
    for r in rows:
        cat = r.get("category") or ""
        if not cat:
            continue
        result[cat] = {
            "total_count": int(r.get("total_count") or 0),
            "valid_count": int(r.get("valid_count") or 0),
            "contact_count": int(r.get("contact_count") or 0),
            "solved_count": int(r.get("solved_count") or 0),
            "satisfied_count": int(r.get("satisfied_count") or 0),
            "basic_satisfied_count": int(r.get("basic_satisfied_count") or 0),
        }
    return result


def _query_finished_count(conn, start_dt: datetime, end_dt: datetime) -> int:
    """
    在指定时间窗口内，按“办结时间”统计四类合计的办结件数。
    注意：这里统计口径是 `办结时间` 落在 [start_dt, end_dt) 内。
    """
    table = get_table_name()
    placeholders = ", ".join(["%s"] * len(EMERGENCY_CATEGORIES))

    sql = f"""
        SELECT COUNT(*) AS finished_count
        FROM {table}
        WHERE `办结时间` IS NOT NULL
          AND `办结时间` >= %s
          AND `办结时间` < %s
          AND `一级分类` IN ({placeholders});
    """
    params: List = [start_dt, end_dt] + EMERGENCY_CATEGORIES
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone() or {}

    return int(row.get("finished_count") or 0)


def get_emergency_category_stats(date_str: str) -> EmergencySummaryResult:
    """
    获取紧急敏感专报总指标（供暖/扬言/消防安全/供水 四类合并）：

    - 本期四类合计受理量 & 上期四类合计受理量
    - 与上期相比增减件数、增减比例
    - 办结件数（按“办结时间”计算）
    - 有效回访数、响应率、解决率、满意率
    - 各分类的件数拆分（含本期、上期、差值）

    统计窗口：
      报表日期 D → [D-1 12:00, D 12:00)
      上一统计期 → [D-2 12:00, D-1 12:00)
    """
    try:
        d = parse_date(date_str)
    except ValueError:
        raise BusinessError("日期格式必须为 YYYY-MM-DD，例如 '2025-05-01'")

    date_str = format_date(d)
    yesterday = get_yesterday(d)
    yesterday_str = format_date(yesterday)

    # 本期 / 上期 时间窗口
    cur_start, cur_end = _get_noon_range_for_date(date_str)
    last_start, last_end = _get_noon_range_for_date(yesterday_str)

    conn = get_connection()
    try:
        # 按一级分类查本期、上期的原始计数（按创建时间）
        cur_map = _query_category_raw_stats(conn, cur_start, cur_end)
        last_map = _query_category_raw_stats(conn, last_start, last_end)

        # 按办结时间统计四类合计办结件数
        finished = _query_finished_count(conn, cur_start, cur_end)

        # ===== 1. 汇总整体指标 =====
        total = 0
        last_total = 0
        valid = contact = solved = satisfied = basic_satisfied = 0

        categories_list: List[EmergencyCategoryStats] = []

        for cat in EMERGENCY_CATEGORIES:
            cur_row = cur_map.get(cat, {
                "total_count": 0,
                "valid_count": 0,
                "contact_count": 0,
                "solved_count": 0,
                "satisfied_count": 0,
                "basic_satisfied_count": 0,
            })
            last_row = last_map.get(cat, {
                "total_count": 0,
                "valid_count": 0,
                "contact_count": 0,
                "solved_count": 0,
                "satisfied_count": 0,
                "basic_satisfied_count": 0,
            })

            cur_total = cur_row["total_count"]
            last_cat_total = last_row["total_count"]
            cat_diff = cur_total - last_cat_total

            # 总体合计
            total += cur_total
            last_total += last_cat_total
            valid += cur_row["valid_count"]
            contact += cur_row["contact_count"]
            solved += cur_row["solved_count"]
            satisfied += cur_row["satisfied_count"]
            basic_satisfied += cur_row["basic_satisfied_count"]

            # 分类拆分数据
            categories_list.append(
                {
                    "category": cat,
                    "total": cur_total,
                    "last_total": last_cat_total,
                    "diff": cat_diff,
                }
            )

        diff = total - last_total
        diff_rate = (diff / last_total) if last_total > 0 else 0.0

        # ===== 2. 计算三率（整体）=====
        if valid > 0:
            response_rate = contact / valid
            solved_rate = solved / valid
            satisfied_rate = (satisfied + 0.9 * basic_satisfied) / valid
        else:
            response_rate = solved_rate = satisfied_rate = 0.0

        return {
            "date": date_str,
            "period_start": cur_start.strftime("%Y-%m-%d %H:%M:%S"),
            "period_end": cur_end.strftime("%Y-%m-%d %H:%M:%S"),
            "last_period_start": last_start.strftime("%Y-%m-%d %H:%M:%S"),
            "last_period_end": last_end.strftime("%Y-%m-%d %H:%M:%S"),

            "total": total,
            "last_total": last_total,
            "diff": diff,
            "diff_rate": diff_rate,

            "finished": finished,

            "valid": valid,
            "contact": contact,
            "solved": solved,
            "satisfied": satisfied,
            "basic_satisfied": basic_satisfied,

            "response_rate": response_rate,
            "solved_rate": solved_rate,
            "satisfied_rate": satisfied_rate,

            "categories": categories_list,
        }
    finally:
        release_connection(conn)


def get_emergency_appeals_for_date(date_str: str) -> EmergencyAppealResult:
    """
    获取紧急敏感诉求的主要内容和处理结果：
       - 限定一级分类为【供暖、扬言、消防安全、供水】
       - 时间窗口：[前一日12:00, 当日12:00)
       - 按创建时间排序
    """
    try:
        d = parse_date(date_str)
    except ValueError:
        raise BusinessError("日期格式必须为 YYYY-MM-DD，例如 '2025-05-01'")

    date_str = format_date(d)
    start_dt, end_dt = _get_noon_range_for_date(date_str)

    table = get_table_name()
    conn = get_connection()
    try:
        placeholders = ", ".join(["%s"] * len(EMERGENCY_CATEGORIES))
        sql = f"""
            SELECT
                `创建时间`           AS created_at,
                `二级承办单位简称`   AS dept,
                `一级分类`           AS category,
                `主要内容`           AS content,
                `处理结果`           AS result   -- TODO: 如字段名不同，请改为实际列名
            FROM {table}
            WHERE `创建时间` >= %s
              AND `创建时间` < %s
              AND `一级分类` IN ({placeholders})
            ORDER BY `创建时间` ASC, `二级承办单位简称` ASC;
        """
        params: List = [start_dt, end_dt] + EMERGENCY_CATEGORIES
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall() or []

        items: List[EmergencyAppealItem] = []
        for r in rows:
            created_at = r.get("created_at")
            items.append(
                {
                    "datetime": created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "",
                    "department": r.get("dept") or "",
                    "category": r.get("category") or "",
                    "content": r.get("content") or "",
                    "result": r.get("result") or "",
                }
            )

        return {
            "date": date_str,
            "period_start": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "period_end": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "items": items,
        }
    finally:
        release_connection(conn)
