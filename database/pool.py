"""PostgreSQL 连接池管理"""

import atexit
import logging
import os
from contextlib import contextmanager
from threading import Lock
from typing import Optional, Generator

from psycopg2 import pool
from psycopg2.extras import RealDictCursor

_logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "database": os.environ.get("DB_NAME", "splatoon3"),
    "user": os.environ.get("DB_USER", "dev"),
    "password": os.environ.get("DB_PASSWORD", "dev123"),
}

_pool: Optional[pool.ThreadedConnectionPool] = None
_pool_lock = Lock()


def _get_pool() -> pool.ThreadedConnectionPool:
    """获取或初始化连接池（懒加载，线程安全）"""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                try:
                    _pool = pool.ThreadedConnectionPool(minconn=1, maxconn=10, **DB_CONFIG)
                    atexit.register(close_pool)
                    _logger.info("Database connection pool initialized")
                except Exception as e:
                    _logger.critical(f"Failed to initialize database pool: {e}")
                    raise
    return _pool


def get_connection():
    """从连接池获取数据库连接"""
    try:
        return _get_pool().getconn()
    except pool.PoolError as exc:
        raise RuntimeError("数据库连接池不可用或已耗尽") from exc


def release_connection(conn) -> None:
    """释放数据库连接回连接池"""
    if conn is None:
        return
    if _pool and getattr(conn, "closed", 1) == 0:
        _pool.putconn(conn)
    else:
        conn.close()


def close_pool() -> None:
    """关闭连接池（应用退出时调用）"""
    global _pool
    if _pool:
        _pool.closeall()
        _logger.info("Database connection pool closed")
        _pool = None


@contextmanager
def get_cursor(dict_cursor: bool = True) -> Generator:
    """
    获取数据库游标的上下文管理器

    Args:
        dict_cursor: 是否返回字典格式的结果

    Yields:
        数据库游标
    """
    conn = get_connection()
    cursor = None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor if dict_cursor else None)
        yield cursor
        conn.commit()
    except Exception as e:
        _logger.error(f"Database transaction error: {e}", exc_info=True)
        conn.rollback()
        raise
    finally:
        if cursor is not None and not cursor.closed:
            cursor.close()
        release_connection(conn)
