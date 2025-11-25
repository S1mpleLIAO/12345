from __future__ import annotations
from config.loader import config
from datetime import date
from typing import Any, Dict, List
from calendar import monthrange
from db.connection import get_connection, release_connection
from db.table import get_table_name
from utils.dates import parse_date, format_date, get_yesterday
from utils.exceptions import BusinessError
from models.dailyreport_types import (
    DeptAssessmentRecord,
    RateStats,
    StreetCount,
    StreetRanks,
    DailyStatsResult,
    AppealItem,
    AppealTop5Result,
    EnterpriseAppealItem,
    EnterpriseAppealResult,
    DailyReportFullData,
    AssessmentPeriodData,
    AssessmentResult,
    AssessmentRankResult,
    StreetAssessmentResult,
    UnitAssessmentResult,
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


def get_full_daily_report_data(date_str: str) -> DailyReportFullData:
    """
    组合调用三个基础统计服务，返回日报所需的所有数据。
    """
    # 1. 获取基础统计 (总量、三率、街道排名)
    stats = get_daily_stats_for_date(date_str)

    # 2. 获取 Top5 诉求
    top5 = get_top5_appeal_types_for_date(date_str)

    # 3. 获取企业诉求
    enterprise = get_enterprise_appeals_for_date(date_str)

    return {
        "stats": stats,
        "top5": top5,
        "enterprise": enterprise,
    }


def _calc_last_month(year: int, month: int) -> tuple[int, int]:
    """返回上个月的 (year, month)"""
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _calc_two_months_ago(year: int, month: int) -> tuple[int, int]:
    """返回上上个月的 (year, month)"""
    if month == 1:
        return year - 1, 11
    if month == 2:
        return year - 1, 12
    return year, month - 2


def _safe_day(year: int, month: int, day: int) -> int:
    """确保 day 不超过该月最大天数（例如 3月31 对比 2月只有28天）"""
    last_day = monthrange(year, month)[1]
    return min(day, last_day)


def _query_period_stats(start: date, end: date) -> AssessmentPeriodData:
    """
    对指定考核期统计：
      - 总受理量 total
      - 解决率 solved_rate
      - 满意率 satisfied_rate
    """
    table = get_table_name()
    start_str = format_date(start)
    end_str = format_date(end)

    sql = f"""
        SELECT
            COUNT(*) AS total_count,
            SUM(CASE WHEN `是否解决` = '是' THEN 1 ELSE 0 END) AS solved_count,
            SUM(CASE WHEN `是否满意` = '是' THEN 1 ELSE 0 END) AS satisfied_count
        FROM {table}
        WHERE `日期` BETWEEN %s AND %s;
    """

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (start_str, end_str))
            row = cur.fetchone() or {}
    finally:
        conn.close()

    total = int(row.get("total_count") or 0)
    solved = int(row.get("solved_count") or 0)
    satisfied = int(row.get("satisfied_count") or 0)

    solved_rate = solved / total if total else 0.0
    satisfied_rate = satisfied / total if total else 0.0

    return {
        "start_date": start_str,
        "end_date": end_str,
        "total": total,
        "solved_rate": solved_rate,
        "satisfied_rate": satisfied_rate,
    }


def get_assessment_data_for_date(date_str: str) -> AssessmentResult:
    """
    输入：任意日期 YYYY-MM-DD（例如 2025-03-15）

    输出：
      - 本考核期：上个月19日 ~ 当日
      - 上一考核期：上上个月19日 ~ 上个月同日（若该月无此日，则用该月最后一天）

    仅返回各考核期原始指标，不包含具体排名数据。
    """
    try:
        d = parse_date(date_str)
    except ValueError:
        raise BusinessError("日期格式必须为 YYYY-MM-DD，例如 '2025-03-15'")

    year = d.year
    month = d.month
    day = d.day

    # 本考核期：上个月19日 ~ 当日
    last_month_year, last_month = _calc_last_month(year, month)
    this_start = date(last_month_year, last_month, 19)
    this_end = d

    # 上一考核期：上上个月19日 ~ 上个月“同日”(或该月最后一天)
    two_ago_year, two_ago_month = _calc_two_months_ago(year, month)
    last_start = date(two_ago_year, two_ago_month, 19)
    last_end_day = _safe_day(last_month_year, last_month, day)
    last_end = date(last_month_year, last_month, last_end_day)

    this_period = _query_period_stats(this_start, this_end)
    last_period = _query_period_stats(last_start, last_end)

    # 已移除排名计算

    month_label = f"{year:04d}-{month:02d}"

    return {
        "date": format_date(d),
        "month_label": month_label,
        "this_period": this_period,
        "last_period": last_period,
    }


def _process_rank_data(rows_map: Dict[str, dict], whitelist: List[str]) -> List[DeptAssessmentRecord]:
    """
    通用清洗函数：
    1. 遍历白名单，确保输出列表长度 == len(whitelist)。
    2. 缺失数据填 0。
    3. 计算综合成绩并排序。
    """
    records: List[DeptAssessmentRecord] = []
    
    # 1. 严格遍历白名单，确保不漏、不杂
    for name in whitelist:
        row = rows_map.get(name, {})
        
        total = int(row.get("total_count") or 0)
        solved = int(row.get("solved_count") or 0)
        satisfied = int(row.get("satisfied_count") or 0)
        
        solved_rate = solved / total if total > 0 else 0.0
        satisfied_rate = satisfied / total if total > 0 else 0.0
        
        records.append({
            "department": name,
            "total": total,
            "solved": solved,
            "satisfied": satisfied,
            "solved_rate": solved_rate,
            "satisfied_rate": satisfied_rate,
            "score": 0.0  # 占位
        })

    # 2. 计算综合成绩 (仅在当前组内归一化)
    max_total = max((r["total"] for r in records), default=0)
    
    for r in records:
        if max_total > 0:
            total_norm = r["total"] / max_total
        else:
            total_norm = 0.0
        
        # 综合成绩公式
        score = (total_norm * 0.10 + r["solved_rate"] * 0.50 + r["satisfied_rate"] * 0.40) * 100
        r["score"] = round(score, 1)

    # 3. 排序：分数优先，受理量其次
    records.sort(key=lambda x: (x["score"], x["total"]), reverse=True)
    
    return records

def _query_raw_period_data(start: date, end: date) -> Dict[str, dict]:
    """
    查询指定时间段内所有部门的原始数据，返回 {部门名: {数据}} 字典。
    """
    table = get_table_name()
    start_str = format_date(start)
    end_str = format_date(end)
    
    sql = f"""
        SELECT
            `处置部门` AS dept,
            COUNT(*) AS total_count,
            SUM(CASE WHEN `是否解决` = '是' THEN 1 ELSE 0 END) AS solved_count,
            SUM(CASE WHEN `是否满意` = '是' THEN 1 ELSE 0 END) AS satisfied_count
        FROM {table}
        WHERE `日期` BETWEEN %s AND %s
        GROUP BY `处置部门`;
    """
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (start_str, end_str))
            rows = cur.fetchall() or []
    finally:
        release_connection(conn)
        
    return {r["dept"]: r for r in rows}

def _get_period_dates(date_str: str):
    """计算考核期时间：上个月19日 ~ 当日"""
    try:
        d = parse_date(date_str)
    except ValueError:
        raise BusinessError("日期格式错误")
        
    year = d.year
    month = d.month
    
    # 上个月的年份和月份
    last_year = year - 1 if month == 1 else year
    last_month = 12 if month == 1 else month - 1
    
    start_date = date(last_year, last_month, 19)
    end_date = d
    
    return start_date, end_date

# === 独立工具服务 1：获取街道数据 ===
def get_street_assessment_data(date_str: str) -> StreetAssessmentResult:
    start_date, end_date = _get_period_dates(date_str)
    
    # 1. 查全量数据
    rows_map = _query_raw_period_data(start_date, end_date)
    
    # 2. 只清洗街道 (16个)
    records = _process_rank_data(rows_map, config.raw_streets)
    
    return {
        "date": date_str,
        "period_start": format_date(start_date),
        "period_end": format_date(end_date),
        "records": records
    }

# === 独立工具服务 2：获取区直单位数据 ===
def get_unit_assessment_data(date_str: str) -> UnitAssessmentResult:
    start_date, end_date = _get_period_dates(date_str)
    
    # 1. 查全量数据
    rows_map = _query_raw_period_data(start_date, end_date)
    
    # 2. 只清洗区直单位 (33个)
    records = _process_rank_data(rows_map, config.raw_units)
    
    return {
        "date": date_str,
        "period_start": format_date(start_date),
        "period_end": format_date(end_date),
        "records": records
    }