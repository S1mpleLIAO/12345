from __future__ import annotations

import pymysql
from pymysql.cursors import DictCursor

from config.loader import config


def get_connection():
    """
    获取 MySQL 连接。
    """
    return pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
        cursorclass=DictCursor,
        autocommit=True,
        charset="utf8mb4",
    )
