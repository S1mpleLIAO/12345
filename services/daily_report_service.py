from __future__ import annotations

from config.loader import config
from datetime import date, datetime, time, timedelta
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
    StreetAssessmentResult,
    UnitAssessmentResult,
)

# ================== 通用小工具 ==================


def _calc_rates(row: Dict[str, Any]) -> RateStats:
    """
    按“有效回访”为分母计算解决率 & 满意率：
      解决率 = 已解决数 / 有效回访数
      满意率 = (满意数 + 0.9 * 基本满意数) / 有效回访数
    """
    total = int(row.get("total_count") or 0)  # 总受理量
    valid = int(row.get("valid_count") or 0)  # 有效回访

    solved = int(row.get("solved_count") or 0)
    satisfied = int(row.get("satisfied_count") or 0)
    basic_satisfied = int(row.get("basic_satisfied_count") or 0)

    if valid > 0:
        solved_rate = solved / valid
        satisfied_rate = (satisfied + 0.9 * basic_satisfied) / valid
    else:
        solved_rate = 0.0
        satisfied_rate = 0.0

    return {
        "total": total,
        "solved": solved,
        "satisfied": satisfied,
        "solved_rate": solved_rate,
        "satisfied_rate": satisfied_rate,
    }


def _get_noon_range_for_date(date_str: str) -> tuple[datetime, datetime]:
    """
    把报表日期（例如 '2025-05-02'）映射为：
    [2025-05-01 12:00:00, 2025-05-02 12:00:00)
    这样的时间区间，用于日报统计。
    """
    d = parse_date(date_str)
    end_dt = datetime.combine(d, time(12, 0, 0))
    start_dt = end_dt - timedelta(days=1)
    return start_dt, end_dt


# ================== 每日基础统计 ==================


def _query_stats_for_date(conn, date_str: str) -> RateStats:
    """
    使用创建时间的 12 点滚动窗口统计：
    [前一日12:00, 当日12:00) 的数据。
    """
    table = get_table_name()
    start_dt, end_dt = _get_noon_range_for_date(date_str)

    sql = f"""
        SELECT
            COUNT(*) AS total_count,
            -- 有效回访：是否有效回访 = '是'
            SUM(CASE WHEN `是否有效回访` = '是'
                     THEN 1 ELSE 0 END) AS valid_count,
            -- 已解决（在有效回访内）
            SUM(CASE WHEN `是否解决` = '是'
                      AND `是否有效回访` = '是'
                     THEN 1 ELSE 0 END) AS solved_count,
            -- 满意数（有效回访且满意）
            SUM(CASE WHEN `是否有效回访` = '是'
                      AND `是否满意` = '满意'
                     THEN 1 ELSE 0 END) AS satisfied_count,
            -- 基本满意数（有效回访且基本满意）
            SUM(CASE WHEN `是否有效回访` = '是'
                      AND `是否满意` = '基本满意'
                     THEN 1 ELSE 0 END) AS basic_satisfied_count
        FROM {table}
        WHERE `创建时间` >= %s
          AND `创建时间` < %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (start_dt, end_dt))
        row = cur.fetchone() or {}

    return _calc_rates(row)


def _query_street_ranks_for_date(conn, date_str: str) -> StreetRanks:
    """
    查询指定日报日期窗口内“二级承办单位简称”的出现次数 Top3 / Bottom3。
    区间：前一日12:00 ~ 当日12:00。
    """
    table = get_table_name()
    start_dt, end_dt = _get_noon_range_for_date(date_str)

    sql = f"""
        SELECT
            `二级承办单位简称` AS dept_name,
            COUNT(*) AS cnt
        FROM {table}
        WHERE `创建时间` >= %s
          AND `创建时间` < %s
        GROUP BY `二级承办单位简称`
        ORDER BY cnt DESC;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (start_dt, end_dt))
        rows = cur.fetchall() or []

    all_list: List[StreetCount] = [
        {"street_name": r["dept_name"], "count": int(r["cnt"])} for r in rows
    ]

    top3 = all_list[:3]
    bottom3 = all_list[-3:] if len(all_list) >= 3 else all_list

    return {"top3": top3, "bottom3": bottom3}


def get_daily_stats_for_date(date_str: str) -> DailyStatsResult:
    """
    日报：今日 = [date-1 12:00, date 12:00)，昨日 = 再往前一天同窗口。
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


# ================== 诉求类型 Top5 ==================


def get_top5_appeal_types_for_date(date_str: str) -> AppealTop5Result:
    """
    在日报窗口内统计一级分类 Top5。
    """
    try:
        d = parse_date(date_str)
    except ValueError:
        raise BusinessError("日期格式必须为 YYYY-MM-DD，例如 '2025-01-01'")

    date_str = format_date(d)
    start_dt, end_dt = _get_noon_range_for_date(date_str)

    table = get_table_name()
    conn = get_connection()
    try:
        sql_total = f"""
            SELECT COUNT(*) AS total_count
            FROM {table}
            WHERE `创建时间` >= %s
              AND `创建时间` < %s;
        """
        with conn.cursor() as cur:
            cur.execute(sql_total, (start_dt, end_dt))
            row = cur.fetchone() or {}
        total = int(row.get("total_count") or 0)

        if total == 0:
            return {"date": date_str, "total": 0, "items": []}

        sql_group = f"""
            SELECT
                `一级分类` AS type_name,
                COUNT(*) AS cnt
            FROM {table}
            WHERE `创建时间` >= %s
              AND `创建时间` < %s
            GROUP BY `一级分类`
            ORDER BY cnt DESC
            LIMIT 5;
        """
        with conn.cursor() as cur:
            cur.execute(sql_group, (start_dt, end_dt))
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

        return {"date": date_str, "total": total, "items": items}
    finally:
        release_connection(conn)


# ================== 企业诉求列表 ==================


def get_enterprise_appeals_for_date(date_str: str) -> EnterpriseAppealResult:
    """
    日报窗口内的企业诉求明细。
    """
    try:
        d = parse_date(date_str)
    except ValueError:
        raise BusinessError("日期格式必须为 YYYY-MM-DD，例如 '2025-01-01'")

    date_str = format_date(d)
    start_dt, end_dt = _get_noon_range_for_date(date_str)

    table = get_table_name()
    conn = get_connection()
    try:
        sql = f"""
            SELECT
                DATE(`创建时间`)       AS dt,
                `二级承办单位简称`     AS dept,
                `一级分类`             AS appeal_type,
                `主要内容`             AS content
            FROM {table}
            WHERE `创建时间` >= %s
              AND `创建时间` < %s
              AND (
                    `一级分类` LIKE %s
                 OR `主要内容` LIKE %s
              )
            ORDER BY `创建时间` ASC, `二级承办单位简称` ASC;
        """
        like_pattern = "%企业%"

        with conn.cursor() as cur:
            cur.execute(sql, (start_dt, end_dt, like_pattern, like_pattern))
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

        return {"date": date_str, "total": len(items), "items": items}
    finally:
        release_connection(conn)


def get_full_daily_report_data(date_str: str) -> DailyReportFullData:
    stats = get_daily_stats_for_date(date_str)
    top5 = get_top5_appeal_types_for_date(date_str)
    enterprise = get_enterprise_appeals_for_date(date_str)

    return {"stats": stats, "top5": top5, "enterprise": enterprise}


# ================== 考核期基础工具 ==================


def _calc_last_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _calc_two_months_ago(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 11
    if month == 2:
        return year - 1, 12
    return year, month - 2


def _safe_day(year: int, month: int, day: int) -> int:
    last_day = monthrange(year, month)[1]
    return min(day, last_day)


def _query_period_stats(start: date, end: date) -> AssessmentPeriodData:
    """
    考核期汇总：
      统计时间段为 [start 00:00, end 12:00)。
    """
    table = get_table_name()
    start_dt = datetime.combine(start, time(0, 0, 0))
    end_dt = datetime.combine(end, time(12, 0, 0))

    start_str = format_date(start)
    end_str = format_date(end)

    sql = f"""
        SELECT
            COUNT(*) AS total_count,
            -- 有效回访
            SUM(CASE WHEN `是否有效回访` = '是'
                     THEN 1 ELSE 0 END) AS valid_count,
            -- 已解决（有效回访内）
            SUM(CASE WHEN `是否解决` = '是'
                      AND `是否有效回访` = '是'
                     THEN 1 ELSE 0 END) AS solved_count,
            -- 满意数
            SUM(CASE WHEN `是否有效回访` = '是'
                      AND `是否满意` = '满意'
                     THEN 1 ELSE 0 END) AS satisfied_count,
            -- 基本满意数
            SUM(CASE WHEN `是否有效回访` = '是'
                      AND `是否满意` = '基本满意'
                     THEN 1 ELSE 0 END) AS basic_satisfied_count
        FROM {table}
        WHERE `创建时间` >= %s
          AND `创建时间` < %s;
    """

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (start_dt, end_dt))
            row = cur.fetchone() or {}
    finally:
        release_connection(conn)

    total = int(row.get("total_count") or 0)
    valid = int(row.get("valid_count") or 0)
    solved = int(row.get("solved_count") or 0)
    satisfied = int(row.get("satisfied_count") or 0)
    basic_satisfied = int(row.get("basic_satisfied_count") or 0)

    if valid > 0:
        solved_rate = solved / valid
        satisfied_rate = (satisfied + 0.9 * basic_satisfied) / valid
    else:
        solved_rate = 0.0
        satisfied_rate = 0.0

    return {
        "start_date": start_str,
        "end_date": end_str,
        "total": total,
        "solved_rate": solved_rate,
        "satisfied_rate": satisfied_rate,
    }


def get_assessment_data_for_date(date_str: str) -> AssessmentResult:
    """
    本考核期：上个月19日00:00 ~ 当日12:00
    上一考核期：上上个月19日00:00 ~ 上个月同日(或月底)12:00
    """
    try:
        d = parse_date(date_str)
    except ValueError:
        raise BusinessError("日期格式必须为 YYYY-MM-DD，例如 '2025-03-15'")

    year = d.year
    month = d.month
    day = d.day

    last_month_year, last_month = _calc_last_month(year, month)
    this_start = date(last_month_year, last_month, 19)
    this_end = d

    two_ago_year, two_ago_month = _calc_two_months_ago(year, month)
    last_start = date(two_ago_year, two_ago_month, 19)
    last_end_day = _safe_day(last_month_year, last_month, day)
    last_end = date(last_month_year, last_month, last_end_day)

    this_period = _query_period_stats(this_start, this_end)
    last_period = _query_period_stats(last_start, last_end)

    month_label = f"{year:04d}-{month:02d}"

    return {
        "date": format_date(d),
        "month_label": month_label,
        "this_period": this_period,
        "last_period": last_period,
    }


# ================== 部门排名 & 汇总（街道 / 区直单位） ==================


def _process_rank_data(rows_map: Dict[str, dict], whitelist: List[str]) -> List[DeptAssessmentRecord]:
    """
    清洗并计算部门考核数据：

    输出字段（对应表头）：
      序号（外部生成）
      承办单位 -> department
      受理量   -> total
      办结量   -> closed
      有效回访 -> valid
      联系数   -> contact
      解决数   -> solved
      满意数   -> satisfied
      基本满意 -> basic_satisfied
      响应率   -> response_rate
      解决率   -> solved_rate
      满意率   -> satisfied_rate
      综合成绩 -> score
    """
    records: List[DeptAssessmentRecord] = []

    for name in whitelist:
        row = rows_map.get(name, {})

        total = int(row.get("total_count") or 0)
        closed = int(row.get("closed_count") or 0)   # 新增：办结量
        valid = int(row.get("valid_count") or 0)
        contact = int(row.get("contact_count") or 0)
        solved = int(row.get("solved_count") or 0)
        satisfied = int(row.get("satisfied_count") or 0)
        basic_satisfied = int(row.get("basic_satisfied_count") or 0)

        if valid > 0:
            response_rate = contact / valid
            solved_rate = solved / valid
            satisfied_rate = (satisfied + 0.9 * basic_satisfied) / valid
        else:
            response_rate = 0.0
            solved_rate = 0.0
            satisfied_rate = 0.0

        records.append(
            {
                "department": name,
                "total": total,
                "closed": closed,
                "valid": valid,
                "contact": contact,
                "solved": solved,
                "satisfied": satisfied,
                "basic_satisfied": basic_satisfied,
                "response_rate": response_rate,
                "solved_rate": solved_rate,
                "satisfied_rate": satisfied_rate,
                "score": 0.0,  # 占位，下面再算
            }
        )

    # 综合成绩： (响应率*0.1 + 满意率*0.4 + 解决率*0.5) * 100
    for r in records:
        score = (
            r["response_rate"] * 0.10
            + r["satisfied_rate"] * 0.40
            + r["solved_rate"] * 0.50
        ) * 100
        r["score"] = round(score, 1)

    # 排序：综合成绩优先，其次受理量
    records.sort(key=lambda x: (x["score"], x["total"]), reverse=True)

    return records


def _calc_summary_from_records(records: List[DeptAssessmentRecord]) -> DeptAssessmentRecord:
    """
    生成“汇总”行：
      - total/closed/valid/contact/solved/satisfied/basic_satisfied 求和
      - response_rate/solved_rate/satisfied_rate/score 取算术平均
    """
    if not records:
        return {
            "department": "汇总",
            "total": 0,
            "closed": 0,
            "valid": 0,
            "contact": 0,
            "solved": 0,
            "satisfied": 0,
            "basic_satisfied": 0,
            "response_rate": 0.0,
            "solved_rate": 0.0,
            "satisfied_rate": 0.0,
            "score": 0.0,
        }

    n = len(records)

    total_sum = sum(r["total"] for r in records)
    closed_sum = sum(r["closed"] for r in records)
    valid_sum = sum(r["valid"] for r in records)
    contact_sum = sum(r["contact"] for r in records)
    solved_sum = sum(r["solved"] for r in records)
    satisfied_sum = sum(r["satisfied"] for r in records)
    basic_satisfied_sum = sum(r["basic_satisfied"] for r in records)

    avg_response_rate = sum(r["response_rate"] for r in records) / n
    avg_solved_rate = sum(r["solved_rate"] for r in records) / n
    avg_satisfied_rate = sum(r["satisfied_rate"] for r in records) / n
    avg_score = sum(r["score"] for r in records) / n

    return {
        "department": "汇总",
        "total": total_sum,
        "closed": closed_sum,
        "valid": valid_sum,
        "contact": contact_sum,
        "solved": solved_sum,
        "satisfied": satisfied_sum,
        "basic_satisfied": basic_satisfied_sum,
        "response_rate": avg_response_rate,
        "solved_rate": avg_solved_rate,
        "satisfied_rate": avg_satisfied_rate,
        "score": round(avg_score, 1),
    }

def _query_raw_period_data(start: date, end: date) -> Dict[str, dict]:
    """
    查询指定时间段内所有部门的原始数据，返回 {部门名: {数据}} 字典。

    时间口径：
      - 受理量/有效回访/联系数/解决数/满意数/基本满意：
          使用 创建时间 ∈ [start 00:00, end 12:00)
      - 办结量：
          使用 办结时间 ∈ [上个月10日 00:00, end 12:00)
    """
    table = get_table_name()

    # 考核期统计使用的创建时间窗口
    start_dt = datetime.combine(start, time(0, 0, 0))
    end_dt = datetime.combine(end, time(12, 0, 0))

    # 办结量使用的办结时间窗口：[last_month_10 00:00, end 12:00)
    year = end.year
    month = end.month
    if month == 1:
        closed_year = year - 1
        closed_month = 12
    else:
        closed_year = year
        closed_month = month - 1
    closed_start_date = date(closed_year, closed_month, 10)
    closed_start_dt = datetime.combine(closed_start_date, time(0, 0, 0))
    closed_end_dt = end_dt  # 同 end 的 12:00

    conn = get_connection()
    try:
        rows_map: Dict[str, dict] = {}

        with conn.cursor() as cur:
            # 1) 先查考核期内（按创建时间）的各种统计
            sql_main = f"""
                SELECT
                    `二级承办单位简称` AS dept,
                    COUNT(*) AS total_count,
                    -- 有效回访
                    SUM(CASE WHEN `是否有效回访` = '是'
                             THEN 1 ELSE 0 END) AS valid_count,
                    -- 联系数（有效回访且联系）
                    SUM(CASE WHEN `是否有效回访` = '是'
                              AND `是否联系` = '是'
                             THEN 1 ELSE 0 END) AS contact_count,
                    -- 已解决（有效回访内）
                    SUM(CASE WHEN `是否有效回访` = '是'
                              AND `是否解决` = '是'
                             THEN 1 ELSE 0 END) AS solved_count,
                    -- 满意数
                    SUM(CASE WHEN `是否有效回访` = '是'
                              AND `是否满意` = '满意'
                             THEN 1 ELSE 0 END) AS satisfied_count,
                    -- 基本满意数
                    SUM(CASE WHEN `是否有效回访` = '是'
                              AND `是否满意` = '基本满意'
                             THEN 1 ELSE 0 END) AS basic_satisfied_count
                FROM {table}
                WHERE `创建时间` >= %s
                  AND `创建时间` < %s
                GROUP BY `二级承办单位简称`;
            """
            cur.execute(sql_main, (start_dt, end_dt))
            rows = cur.fetchall() or []
            rows_map = {r["dept"]: dict(r) for r in rows}

            # 2) 再查“办结量”（按办结时间窗口）
            sql_closed = f"""
                SELECT
                    `二级承办单位简称` AS dept,
                    COUNT(*) AS closed_count
                FROM {table}
                WHERE `办结时间` >= %s
                  AND `办结时间` < %s
                GROUP BY `二级承办单位简称`;
            """
            cur.execute(sql_closed, (closed_start_dt, closed_end_dt))
            closed_rows = cur.fetchall() or []

            for r in closed_rows:
                dept = r["dept"]
                closed_count = int(r["closed_count"] or 0)
                if dept in rows_map:
                    rows_map[dept]["closed_count"] = closed_count
                else:
                    # 该部门在创建时间窗口内没有工单，但有办结量
                    rows_map[dept] = {
                        "dept": dept,
                        "total_count": 0,
                        "valid_count": 0,
                        "contact_count": 0,
                        "solved_count": 0,
                        "satisfied_count": 0,
                        "basic_satisfied_count": 0,
                        "closed_count": closed_count,
                    }

    finally:
        release_connection(conn)

    return rows_map



def _get_period_dates(date_str: str):
    """
    计算考核期日期边界（用于展示）：
      start_date: 上个月19日
      end_date:   当前日期
    实际统计用 [start 00:00, end 12:00)。
    """
    try:
        d = parse_date(date_str)
    except ValueError:
        raise BusinessError("日期格式错误")

    year = d.year
    month = d.month

    last_year = year - 1 if month == 1 else year
    last_month = 12 if month == 1 else month - 1

    start_date = date(last_year, last_month, 19)
    end_date = d

    return start_date, end_date


# === 独立工具服务 1：获取街道考核期数据 ===
def get_street_assessment_data(date_str: str) -> StreetAssessmentResult:
    start_date, end_date = _get_period_dates(date_str)

    rows_map = _query_raw_period_data(start_date, end_date)
    records = _process_rank_data(rows_map, config.raw_streets)
    summary = _calc_summary_from_records(records)

    return {
        "date": date_str,
        "period_start": format_date(start_date),
        "period_end": format_date(end_date),
        "records": records,
        "summary": summary,
    }


# === 独立工具服务 2：获取区直单位考核期数据 ===
def get_unit_assessment_data(date_str: str) -> UnitAssessmentResult:
    start_date, end_date = _get_period_dates(date_str)

    rows_map = _query_raw_period_data(start_date, end_date)
    records = _process_rank_data(rows_map, config.raw_units)
    summary = _calc_summary_from_records(records)

    return {
        "date": date_str,
        "period_start": format_date(start_date),
        "period_end": format_date(end_date),
        "records": records,
        "summary": summary,
    }
