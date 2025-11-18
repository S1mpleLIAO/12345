from __future__ import annotations

import pymysql
from pymysql.cursors import DictCursor
from queue import Queue
from threading import Lock

from config.loader import config


class MySQLPool:
    def __init__(self, min_conn=1, max_conn=10):
        self.min_conn = min_conn
        self.max_conn = max_conn

        self.pool = Queue(max_conn)
        self.lock = Lock()

        # 初始化最小连接数
        for _ in range(min_conn):
            self.pool.put(self._create_conn())

    def _create_conn(self):
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

    def get_conn(self):
        with self.lock:
            if not self.pool.empty():
                return self.pool.get()
            return self._create_conn()

    def return_conn(self, conn):
        """
        放回连接池。连接池满了则直接关闭连接。
        """
        with self.lock:
            try:
                self.pool.put(conn, block=False)
            except:
                conn.close()


pool = MySQLPool(min_conn=1, max_conn=10)


def get_connection():
    return pool.get_conn()


def release_connection(conn):
    pool.return_conn(conn)
