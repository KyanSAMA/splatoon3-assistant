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
