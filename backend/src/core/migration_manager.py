"""数据库迁移管理器"""

import logging
import os
import aiosqlite
from pathlib import Path

logger = logging.getLogger(__name__)


def get_migrations_dir() -> Path:
    """获取迁移文件目录（支持打包后运行）"""
    env_dir = os.environ.get("MIGRATIONS_DIR")
    if env_dir:
        return Path(env_dir)
    return Path(__file__).resolve().parents[2] / "database" / "migrations"


async def ensure_migration_table(db_path: str) -> None:
    """确保迁移历史表存在"""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY,
                filename TEXT UNIQUE NOT NULL,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def get_applied_migrations(db_path: str) -> set[str]:
    """获取已执行的迁移文件名"""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT filename FROM migration_history")
        rows = await cursor.fetchall()
        return {row[0] for row in rows}


async def record_migration(db_path: str, filename: str) -> None:
    """记录迁移执行"""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO migration_history (filename) VALUES (?)",
            (filename,)
        )
        await db.commit()


async def execute_sql_file(db_path: str, sql_file: Path) -> None:
    """执行 SQL 文件并记录迁移（原子操作）"""
    try:
        sql_content = sql_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise RuntimeError(f"无法读取迁移文件 {sql_file}: {e}") from e

    async with aiosqlite.connect(db_path) as db:
        # 执行迁移 SQL
        await db.executescript(sql_content)
        # 记录迁移（同一连接，executescript 已自动提交）
        await db.execute(
            "INSERT INTO migration_history (filename) VALUES (?)",
            (sql_file.name,)
        )
        await db.commit()


async def run_migrations(db_path: str) -> int:
    """
    执行所有未执行的迁移

    Returns:
        执行的迁移数量
    """
    migrations_dir = get_migrations_dir()
    if not migrations_dir.exists():
        logger.warning(f"迁移目录不存在: {migrations_dir}")
        return 0

    # 确保迁移历史表存在
    await ensure_migration_table(db_path)

    # 获取已执行的迁移
    applied = await get_applied_migrations(db_path)

    # 获取所有迁移文件（按文件名排序）
    migration_files = sorted(migrations_dir.glob("*.sql"))

    executed_count = 0
    for sql_file in migration_files:
        if sql_file.name in applied:
            continue

        logger.info(f"执行迁移: {sql_file.name}")
        try:
            await execute_sql_file(db_path, sql_file)
            executed_count += 1
            logger.info(f"迁移完成: {sql_file.name}")
        except Exception as e:
            logger.error(f"迁移失败: {sql_file.name} - {e}")
            raise

    return executed_count


async def init_database(db_path: str) -> None:
    """
    初始化数据库

    - 如果数据库不存在，创建并执行所有迁移
    - 如果已存在，只执行未执行的迁移
    """
    db_file = Path(db_path)
    is_new = not db_file.exists()

    if is_new:
        # 确保目录存在
        db_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建新数据库: {db_path}")

    count = await run_migrations(db_path)

    if count > 0:
        logger.info(f"已执行 {count} 个迁移")
    elif is_new:
        logger.info("数据库初始化完成")
    else:
        logger.info("数据库已是最新版本")
