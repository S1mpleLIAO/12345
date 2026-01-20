from __future__ import annotations

import pymysql
from pymysql.cursors import DictCursor
from pymysql import err as pymysql_err

from queue import Queue, Empty, Full
from threading import Lock

from config.loader import config


class MySQLPool:
    """
    一个稳健一点的 PyMySQL 连接池：

    - get_conn(): 借出时 ping(reconnect=True)，坏了就重建
    - return_conn(): 归还时检查健康，不健康则丢弃
    - 限制 max_conn：到达上限后 get_conn() 会阻塞等待归还
    """

    def __init__(self, min_conn: int = 1, max_conn: int = 10):
        if min_conn < 0:
            raise ValueError("min_conn must be >= 0")
        if max_conn <= 0:
            raise ValueError("max_conn must be > 0")
        if min_conn > max_conn:
            raise ValueError("min_conn must be <= max_conn")

        self.min_conn = min_conn
        self.max_conn = max_conn

        self.pool: Queue = Queue(max_conn)
        self.lock = Lock()

        # 当前已创建连接数（包含池中 + 借出中）
        self._created = 0

        # 初始化最小连接数
        for _ in range(min_conn):
            conn = self._create_conn()
            self.pool.put(conn)
            self._created += 1

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
            connect_timeout=5,
            read_timeout=30,
            write_timeout=30,
        )

    @staticmethod
    def _is_healthy(conn) -> bool:
        """
        不重连的健康检查：如果已断开/无 sock，会抛异常
        """
        try:
            conn.ping(reconnect=False)
            return True
        except Exception:
            return False

    def _ensure_conn(self, conn):
        """
        借出前确保连接可用：ping(reconnect=True)，失败则重建
        """
        try:
            conn.ping(reconnect=True)
            return conn
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            return self._create_conn()

    def get_conn(self):
        """
        借出连接：
        - 优先从 pool 取
        - pool 空且未到 max：创建新连接
        - pool 空且已到 max：阻塞等待归还
        """
        # 1) 先尝试无阻塞取一个
        try:
            conn = self.pool.get_nowait()
            return self._ensure_conn(conn)
        except Empty:
            pass

        # 2) pool 空：如果还没到 max_conn，可以新建
        with self.lock:
            if self._created < self.max_conn:
                self._created += 1
                conn = self._create_conn()
                return conn

        # 3) 已到 max_conn：必须等有人归还
        conn = self.pool.get()  # 阻塞
        return self._ensure_conn(conn)

    def return_conn(self, conn):
        """
        归还连接：
        - 若连接已坏，直接丢弃并减少 created 计数
        - 若池满（理论上不该满，但保险），也丢弃
        """
        if conn is None:
            return

        # 如果连接已死，丢弃并减少 created
        if not self._is_healthy(conn):
            try:
                conn.close()
            except Exception:
                pass
            with self.lock:
                # 丢弃一个连接 -> created 减 1，后续 get_conn() 可补新
                if self._created > 0:
                    self._created -= 1
            return

        # 正常连接：放回池
        try:
            self.pool.put_nowait(conn)
        except Full:
            # 池满：丢弃这条连接
            try:
                conn.close()
            except Exception:
                pass
            with self.lock:
                if self._created > 0:
                    self._created -= 1


pool = MySQLPool(min_conn=1, max_conn=10)


def get_connection():
    return pool.get_conn()


def release_connection(conn):
    pool.return_conn(conn)
