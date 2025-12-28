-- Splatoon3 数据表 (SQLite)

-- 副武器表
CREATE TABLE IF NOT EXISTS sub_weapon (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    ink_consume REAL,
    zh_name TEXT,
    params TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 特殊武器表
CREATE TABLE IF NOT EXISTS special_weapon (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    zh_name TEXT,
    params TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 主武器表
CREATE TABLE IF NOT EXISTS main_weapon (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    special_point INTEGER NOT NULL CHECK (special_point > 0),
    sub_weapon_code TEXT,
    special_weapon_code TEXT,
    zh_name TEXT,
    weapon_class TEXT,
    distance_class TEXT,
    params TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_main_weapon_code ON main_weapon(code);
CREATE INDEX IF NOT EXISTS idx_main_weapon_sub_weapon_code ON main_weapon(sub_weapon_code);
CREATE INDEX IF NOT EXISTS idx_main_weapon_special_weapon_code ON main_weapon(special_weapon_code);
CREATE INDEX IF NOT EXISTS idx_main_weapon_weapon_class ON main_weapon(weapon_class);
CREATE INDEX IF NOT EXISTS idx_sub_weapon_code ON sub_weapon(code);
CREATE INDEX IF NOT EXISTS idx_special_weapon_code ON special_weapon(code);

-- 装备能力表
CREATE TABLE IF NOT EXISTS skill (
    id INTEGER PRIMARY KEY ,
    code TEXT NOT NULL UNIQUE,
    zh_name TEXT,
    zh_desc TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_skill_code ON skill(code);
CREATE INDEX IF NOT EXISTS idx_skill_zh_name ON skill(zh_name);

-- 地图表
CREATE TABLE IF NOT EXISTS stage (
    id INTEGER PRIMARY KEY ,
    vs_stage_id INTEGER UNIQUE,
    code TEXT NOT NULL UNIQUE,
    zh_name TEXT,
    stage_type TEXT CHECK (stage_type IN ('VS', 'Coop')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stage_code ON stage(code);
CREATE INDEX IF NOT EXISTS idx_stage_vs_stage_id ON stage(vs_stage_id);
CREATE INDEX IF NOT EXISTS idx_stage_stage_type ON stage(stage_type);

-- 用户表
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nsa_id TEXT NOT NULL UNIQUE,
    splatoon_id TEXT,
    session_token TEXT NOT NULL,
    access_token TEXT NOT NULL,
    g_token TEXT NOT NULL,
    bullet_token TEXT NOT NULL,
    user_lang TEXT NOT NULL DEFAULT 'zh-CN',
    user_country TEXT NOT NULL DEFAULT 'JP',
    user_nickname TEXT,
    is_current INTEGER NOT NULL DEFAULT 0 CHECK (is_current IN (0, 1)),
    last_login_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_current ON user(is_current) WHERE is_current = 1;
CREATE INDEX IF NOT EXISTS idx_user_activity ON user(is_current DESC, last_login_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_nsa_id ON user(nsa_id);
CREATE INDEX IF NOT EXISTS idx_user_splatoon_id ON user(splatoon_id);

-- 用户地图胜率表
CREATE TABLE IF NOT EXISTS user_stage_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stage_id INTEGER,
    vs_stage_id INTEGER NOT NULL,
    stage_code TEXT,
    name TEXT NOT NULL,
    last_played_time TEXT,
    win_rate_ar REAL,
    win_rate_cl REAL,
    win_rate_gl REAL,
    win_rate_lf REAL,
    win_rate_tw REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, vs_stage_id)
);

CREATE INDEX IF NOT EXISTS idx_user_stage_record_user_id ON user_stage_record(user_id);
CREATE INDEX IF NOT EXISTS idx_user_stage_record_vs_stage_id ON user_stage_record(vs_stage_id);
