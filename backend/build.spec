# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置
用法: pyinstaller build.spec
"""

import sys
from pathlib import Path

# 项目根目录
BACKEND_DIR = Path(SPECPATH)
PROJECT_ROOT = BACKEND_DIR.parent

block_cipher = None

# 需要打包的数据文件
datas = [
    # SQL 迁移文件
    (str(BACKEND_DIR / 'database' / 'migrations'), 'database/migrations'),
    # 前端构建产物
    (str(PROJECT_ROOT / 'frontend' / 'dist'), 'frontend/dist'),
    # 数据文件（JSON、语言包等，不含数据库）
    (str(PROJECT_ROOT / 'data' / 'json'), 'data/json'),
    (str(PROJECT_ROOT / 'data' / 'langs'), 'data/langs'),
]

# 隐式导入（动态导入的模块）
hiddenimports = [
    'aiosqlite',
    'sqlalchemy.ext.asyncio',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
]

a = Analysis(
    ['run.py'],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='S3Assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 设为 False 可隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='S3Assistant',
)
