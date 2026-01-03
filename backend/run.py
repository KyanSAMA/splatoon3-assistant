#!/usr/bin/env python3
"""
Splatoon3 Assistant 启动入口
用于 PyInstaller 打包
"""

import os
import sys
import socket
import random
from pathlib import Path


def get_base_path() -> Path:
    """获取应用基础路径（支持打包后运行）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return Path(getattr(sys, '_MEIPASS', '.'))  # type: ignore[attr-defined]
    else:
        # 开发环境
        return Path(__file__).resolve().parent


def get_data_dir() -> Path:
    """获取数据存储目录"""
    if getattr(sys, 'frozen', False):
        exe_parent = Path(sys.executable).parent
        # macOS .app bundle: MyApp.app/Contents/MacOS/MyApp
        if exe_parent.name == "MacOS" and exe_parent.parent.name == "Contents":
            # 使用用户 Application Support 目录
            return Path.home() / "Library" / "Application Support" / "Splatoon3Assistant"
        else:
            # Windows / Linux: 可执行文件同级目录
            return exe_parent / "data"
    else:
        # 开发环境：项目 data 目录
        return Path(__file__).resolve().parents[1] / "data"


def setup_paths():
    """设置路径和环境变量"""
    base_path = get_base_path()
    data_dir = get_data_dir()

    # 确保数据目录存在
    data_dir.mkdir(parents=True, exist_ok=True)

    # 数据库路径
    db_path = data_dir / "splatoon3.db"
    os.environ["DB_PATH"] = str(db_path)

    # 迁移目录（打包后在 _MEIPASS 内）
    migrations_dir = base_path / "database" / "migrations"
    os.environ["MIGRATIONS_DIR"] = str(migrations_dir)

    # 添加 base_path 到 Python 路径
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))

    return base_path


def find_available_port(start: int = 49152, end: int = 65535, max_attempts: int = 50) -> int:
    """在指定范围内随机查找可用端口"""
    for _ in range(max_attempts):
        port = random.randint(start, end)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"无法在 {start}-{end} 范围内找到可用端口")


def main():
    """启动应用"""
    setup_paths()

    port = find_available_port()
    url = f"http://127.0.0.1:{port}"
    os.environ["APP_URL"] = url

    print("=" * 50)
    print("  Splatoon3 Assistant")
    print(f"  访问地址: {url}")
    print("=" * 50)

    from main import app
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
