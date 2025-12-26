"""SQLite 异步连接管理"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite

_logger = logging.getLogger(__name__)

# 默认使用 database/data/splatoon3.db，便于集中存放数据文件
DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "data", "splatoon3.db"),
)


def _dict_factory(cursor: aiosqlite.Cursor, row: tuple) -> dict:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


async def _create_connection() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(DB_PATH, timeout=30.0)
    conn.row_factory = _dict_factory
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@asynccontextmanager
async def get_cursor(commit: bool = True) -> AsyncGenerator[aiosqlite.Cursor, None]:
    """
    获取数据库游标的上下文管理器（每次创建独立连接，确保事务隔离）

    Args:
        commit: 是否在成功时提交事务（默认 True，SELECT 可设为 False）
    """
    conn = await _create_connection()
    try:
        cursor = await conn.cursor()
        try:
            yield cursor
            if commit:
                await conn.commit()
        except Exception:
            await conn.rollback()
            _logger.exception("Database transaction error")
            raise
        finally:
            await cursor.close()
    finally:
        await conn.close()


@asynccontextmanager
async def get_connection() -> AsyncGenerator[aiosqlite.Connection, None]:
    """获取独立数据库连接（用于批量操作）"""
    conn = await _create_connection()
    try:
        yield conn
    finally:
        await conn.close()
