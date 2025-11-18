from __future__ import annotations

from typing import List

from db.connection import get_connection, release_connection
from db.table import get_table_name
from utils.dates import parse_date, format_date
from utils.exceptions import BusinessError
from models.types import AppealItem, AppealTop5Result


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