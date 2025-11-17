# utils/dates.py
from __future__ import annotations

from datetime import datetime, date, timedelta


def parse_date(date_str: str) -> date:
    """
    将 'YYYY-MM-DD' 转为 date 对象。
    """
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def format_date(d: date) -> str:
    """
    date -> 'YYYY-MM-DD'
    """
    return d.strftime("%Y-%m-%d")


def get_yesterday(d: date) -> date:
    """
    获取前一天日期。
    """
    return d - timedelta(days=1)
