from __future__ import annotations

from config.loader import config


def get_table_name() -> str:
    """
    返回带反引号的表名，兼容中文名 / 关键字。
    """
    return f"`{config.table}`"
