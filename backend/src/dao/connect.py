"""SQLite 异步连接管理"""

import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite

_logger = logging.getLogger(__name__)

# 默认指向项目 data 目录下的 SQLite 文件，可通过环境变量覆盖
# connect.py 位于 backend/src/dao/，parents[3] 指向 splatoon3-assistant/
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DB = _PROJECT_ROOT / "data" / "splatoon3.db"
DB_PATH = os.environ.get("DB_PATH", str(_DEFAULT_DB))


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
