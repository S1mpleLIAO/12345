from __future__ import annotations

from datetime import datetime, date, timedelta, time
from typing import List, Tuple

from db.connection import get_connection, release_connection
from db.table import get_table_name
from utils.dates import format_date
from utils.exceptions import BusinessError
from models.heatingreport_types import (
    HeatingStats,
    MonthlyStatItem,
    CentralHeatingStats,
    CategoryItem,
    CompanyItem,
    HeatingReportData,
)

# 供暖相关的通用 LIKE 条件（供暖 / 供热）
HEATING_WHERE_FRAGMENT = """
    `创建时间` >= %s AND `创建时间` < %s
    AND (
        (`一级分类` LIKE %s OR `二级分类` LIKE %s OR `三级分类` LIKE %s) OR
        (`一级分类` LIKE %s OR `二级分类` LIKE %s OR `三级分类` LIKE %s)
    )
"""

CENTRAL_HEATING_WHERE_FRAGMENT = """
    `创建时间` >= %s AND `创建时间` < %s
    AND (
        (`一级分类` LIKE %s OR `二级分类` LIKE %s OR `三级分类` LIKE %s) OR
        (`一级分类` LIKE %s OR `二级分类` LIKE %s OR `三级分类` LIKE %s)
    )
"""


def _calc_heating_season(year: int) -> Tuple[date, date]:
    """根据年份计算供暖季起止日期（11-15 至次年 3-15）。"""
    if year < 2000 or year > 2100:
        raise BusinessError("供暖季年份不合法")
    start_date = date(year, 11, 1)
    end_date = date(year + 1, 3, 14)
    return start_date, end_date


def _build_heating_params(start_dt: datetime, end_dt: datetime) -> Tuple:
    """构造供暖/供热相关的 LIKE 查询参数。"""
    like_gongnuan = "%供暖%"
    like_gongre = "%供热%"
    return (
        start_dt,
        end_dt,
        like_gongnuan,
        like_gongnuan,
        like_gongnuan,
        like_gongre,
        like_gongre,
        like_gongre,
    )


def _build_central_heating_params(start_dt: datetime, end_dt: datetime) -> Tuple:
    """构造集中供暖/集中供热相关的 LIKE 查询参数。"""
    like_central_gn = "%集中供暖%"
    like_central_gr = "%集中供热%"
    return (
        start_dt,
        end_dt,
        like_central_gn,
        like_central_gn,
        like_central_gn,
        like_central_gr,
        like_central_gr,
        like_central_gr,
    )


def _calc_rates(
    valid: int, solved: int, satisfied: int, basic_satisfied: int
) -> Tuple[float, float, float]:
    """
    统一计算解决率、满意率、响应率中的解决率+满意率部分。
    响应率因为统计口径不一样（用 contact），在外面单独算。
    """
    if valid <= 0:
        return 0.0, 0.0, 0.0

    solved_rate = solved / valid
    satisfied_rate = (satisfied + 0.9 * basic_satisfied) / valid
    # 第三个返回值预留（方便以后扩展），暂时返回 0.0
    return solved_rate, satisfied_rate, 0.0


def _query_overall_stats(
    conn, table: str, start_dt: datetime, end_dt: datetime
) -> HeatingStats:
    """查询供暖季总体诉求数量和三率数据。"""
    with conn.cursor() as cur:
        sql = f"""
            SELECT
                COUNT(*) AS total_count,
                SUM(CASE WHEN `是否有效回访` = '是' THEN 1 ELSE 0 END) AS valid_count,
                SUM(CASE WHEN `是否有效回访` = '是' AND `是否联系` = '是' THEN 1 ELSE 0 END) AS contact_count,
                SUM(CASE WHEN `是否有效回访` = '是' AND `是否解决` = '是' THEN 1 ELSE 0 END) AS solved_count,
                SUM(CASE WHEN `是否有效回访` = '是' AND `是否满意` = '满意' THEN 1 ELSE 0 END) AS satisfied_count,
                SUM(CASE WHEN `是否有效回访` = '是' AND `是否满意` = '基本满意' THEN 1 ELSE 0 END) AS basic_satisfied_count
            FROM {table}
            WHERE {HEATING_WHERE_FRAGMENT}
        """
        params = _build_heating_params(start_dt, end_dt)
        cur.execute(sql, params)
        row = cur.fetchone() or {}

    total = int(row.get("total_count") or 0)
    valid = int(row.get("valid_count") or 0)
    contact = int(row.get("contact_count") or 0)
    solved = int(row.get("solved_count") or 0)
    satisfied = int(row.get("satisfied_count") or 0)
    basic_satisfied = int(row.get("basic_satisfied_count") or 0)

    if valid > 0:
        solved_rate, satisfied_rate, _ = _calc_rates(
            valid, solved, satisfied, basic_satisfied
        )
        response_rate = contact / valid
    else:
        solved_rate = satisfied_rate = response_rate = 0.0

    start_date, end_date = start_dt.date(), (end_dt - timedelta(days=1)).date()

    return {
        "start_date": format_date(start_date),
        "end_date": format_date(end_date),
        "total": total,
        "solved": solved,
        "satisfied": satisfied,
        "solved_rate": solved_rate,
        "satisfied_rate": satisfied_rate,
        "response_rate": response_rate,
    }


def _query_monthly_stats(
    conn, table: str, start_dt: datetime, end_dt: datetime
) -> List[MonthlyStatItem]:
    """按月聚合供暖诉求数据。"""
    with conn.cursor() as cur:
        sql = f"""
            SELECT
                DATE_FORMAT(`创建时间`, '%%Y-%%m') AS month_label,
                COUNT(*) AS total_count,
                SUM(CASE WHEN `是否有效回访` = '是' THEN 1 ELSE 0 END) AS valid_count,
                SUM(CASE WHEN `是否有效回访` = '是' AND `是否解决` = '是' THEN 1 ELSE 0 END) AS solved_count,
                SUM(CASE WHEN `是否有效回访` = '是' AND `是否满意` = '满意' THEN 1 ELSE 0 END) AS satisfied_count,
                SUM(CASE WHEN `是否有效回访` = '是' AND `是否满意` = '基本满意' THEN 1 ELSE 0 END) AS basic_satisfied_count
            FROM {table}
            WHERE {HEATING_WHERE_FRAGMENT}
            GROUP BY month_label
            ORDER BY month_label;
        """
        params = _build_heating_params(start_dt, end_dt)
        cur.execute(sql, params)
        rows = cur.fetchall() or []

    monthly_list: List[MonthlyStatItem] = []
    for r in rows:
        month_label = r.get("month_label") or ""
        m_total = int(r.get("total_count") or 0)
        m_valid = int(r.get("valid_count") or 0)
        m_solved = int(r.get("solved_count") or 0)
        m_satisfied = int(r.get("satisfied_count") or 0)
        m_basic_sat = int(r.get("basic_satisfied_count") or 0)

        if m_valid > 0:
            m_solved_rate, m_satisfied_rate, _ = _calc_rates(
                m_valid, m_solved, m_satisfied, m_basic_sat
            )
        else:
            m_solved_rate = m_satisfied_rate = 0.0

        monthly_list.append(
            {
                "month": month_label,
                "total": m_total,
                "solved_rate": m_solved_rate,
                "satisfied_rate": m_satisfied_rate,
            }
        )

    return monthly_list


def _query_central_heating_stats(
    conn, table: str, start_dt: datetime, end_dt: datetime, total: int
) -> CentralHeatingStats:
    """集中供暖相关诉求统计。"""
    with conn.cursor() as cur:
        sql = f"""
            SELECT
                COUNT(*) AS total_count,
                SUM(CASE WHEN `是否有效回访` = '是' THEN 1 ELSE 0 END) AS valid_count,
                SUM(CASE WHEN `是否有效回访` = '是' AND `是否解决` = '是' THEN 1 ELSE 0 END) AS solved_count,
                SUM(CASE WHEN `是否有效回访` = '是' AND `是否满意` = '满意' THEN 1 ELSE 0 END) AS satisfied_count,
                SUM(CASE WHEN `是否有效回访` = '是' AND `是否满意` = '基本满意' THEN 1 ELSE 0 END) AS basic_satisfied_count
            FROM {table}
            WHERE {CENTRAL_HEATING_WHERE_FRAGMENT}
        """
        params = _build_central_heating_params(start_dt, end_dt)
        cur.execute(sql, params)
        row = cur.fetchone() or {}

    central_total = int(row.get("total_count") or 0)
    central_valid = int(row.get("valid_count") or 0)
    central_solved = int(row.get("solved_count") or 0)
    central_satisfied = int(row.get("satisfied_count") or 0)
    central_basic_sat = int(row.get("basic_satisfied_count") or 0)

    if central_valid > 0:
        central_solved_rate, central_satisfied_rate, _ = _calc_rates(
            central_valid, central_solved, central_satisfied, central_basic_sat
        )
    else:
        central_solved_rate = central_satisfied_rate = 0.0

    central_ratio = (central_total / total) if total > 0 else 0.0

    return {
        "total": central_total,
        "ratio": central_ratio,
        "solved_rate": central_solved_rate,
        "satisfied_rate": central_satisfied_rate,
    }


def _query_top_categories(
    conn, table: str, start_dt: datetime, end_dt: datetime, total: int
) -> List[CategoryItem]:
    """供暖季诉求高频的三级分类 Top 10。"""
    with conn.cursor() as cur:
        sql = f"""
            SELECT `三级分类` AS category_name, COUNT(*) AS cnt
            FROM {table}
            WHERE {HEATING_WHERE_FRAGMENT}
            GROUP BY `三级分类`
            ORDER BY cnt DESC
            LIMIT 7;
        """
        params = _build_heating_params(start_dt, end_dt)
        cur.execute(sql, params)
        rows = cur.fetchall() or []

    categories: List[CategoryItem] = []
    for idx, r in enumerate(rows, start=1):
        cat_count = int(r.get("cnt") or 0)
        cat_name = r.get("category_name") or ""
        cat_ratio = cat_count / total if total > 0 else 0.0
        categories.append(
            {
                "rank": idx,
                "category_name": cat_name,
                "count": cat_count,
                "ratio": cat_ratio,
            }
        )

    return categories


def _query_company_ranking(
    conn, table: str, start_dt: datetime, end_dt: datetime, total: int
) -> List[CompanyItem]:
    """供暖季各供热公司诉求办理量排行（count > 50）。"""
    with conn.cursor() as cur:
        sql = f"""
            SELECT `供热公司` AS company_name, COUNT(*) AS cnt
            FROM {table}
            WHERE {HEATING_WHERE_FRAGMENT}
              AND `供热公司` IS NOT NULL
              AND TRIM(`供热公司`) <> ''
            GROUP BY `供热公司`
            HAVING cnt > 50
            ORDER BY cnt DESC;
        """
        params = _build_heating_params(start_dt, end_dt)
        cur.execute(sql, params)
        rows = cur.fetchall() or []

    companies: List[CompanyItem] = []
    for idx, r in enumerate(rows, start=1):
        comp_name = (r.get("company_name") or "").strip()
        if not comp_name:
            continue

        comp_count = int(r.get("cnt") or 0)
        comp_ratio = comp_count / total if total > 0 else 0.0

        companies.append({
            "rank": idx,
            "company_name": comp_name,
            "count": comp_count,
            "ratio": comp_ratio,
        })

    return companies



def get_full_heating_report_data(year: int) -> HeatingReportData:
    """
    获取指定年度供暖季的完整统计分析数据。
    """
    # 1. 计算供暖季起止日期
    start_date, end_date = _calc_heating_season(year)
    start_dt = datetime.combine(start_date, time(0, 0, 0))
    end_dt = datetime.combine(
        end_date + timedelta(days=1), time(0, 0, 0)
    )  # 次日0点作为结束边界
    table = get_table_name()

    conn = get_connection()
    try:
        # 2. 整体统计
        heating_stats = _query_overall_stats(conn, table, start_dt, end_dt)
        print(start_dt, end_dt)
        total = heating_stats["total"]

        # 若供暖季内无相关诉求数据，直接返回空结果集
        if total == 0:
            return {
                "stats": heating_stats,
                "monthly": [],
                "central_heating": {
                    "total": 0,
                    "ratio": 0.0,
                    "solved_rate": 0.0,
                    "satisfied_rate": 0.0,
                },
                "categories": [],
                "companies": [],
            }

        # 3. 月度统计
        monthly_list = _query_monthly_stats(conn, table, start_dt, end_dt)

        # 4. 集中供暖统计
        central_stats = _query_central_heating_stats(
            conn, table, start_dt, end_dt, total
        )

        # 5. 分类 Top10
        categories_list = _query_top_categories(conn, table, start_dt, end_dt, total)

        # 6. 公司排行
        companies_list = _query_company_ranking(conn, table, start_dt, end_dt, total)

        # 汇总
        result: HeatingReportData = {
            "stats": heating_stats,
            "monthly": monthly_list,
            "central_heating": central_stats,
            "categories": categories_list,
            "companies": companies_list,
        }
        return result

    finally:
        release_connection(conn)
