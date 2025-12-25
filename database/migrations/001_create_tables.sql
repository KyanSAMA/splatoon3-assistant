-- Splatoon3 数据表

-- 副武器表 (先创建，被主武器表引用)
CREATE TABLE IF NOT EXISTS sub_weapon (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    ink_consume DECIMAL(5,4),
    zh_name VARCHAR(100),
    params JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 特殊武器表 (先创建，被主武器表引用)
CREATE TABLE IF NOT EXISTS special_weapon (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    zh_name VARCHAR(100),
    params JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 主武器表
CREATE TABLE IF NOT EXISTS main_weapon (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    special_point INTEGER NOT NULL CHECK (special_point > 0),
    sub_weapon_code VARCHAR(10),
    special_weapon_code VARCHAR(10),
    zh_name VARCHAR(100),
    weapon_class VARCHAR(50),
    distance_class VARCHAR(50),
    params JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_main_weapon_code ON main_weapon(code);
CREATE INDEX IF NOT EXISTS idx_main_weapon_sub_weapon_code ON main_weapon(sub_weapon_code);
CREATE INDEX IF NOT EXISTS idx_main_weapon_special_weapon_code ON main_weapon(special_weapon_code);
CREATE INDEX IF NOT EXISTS idx_main_weapon_weapon_class ON main_weapon(weapon_class);
CREATE INDEX IF NOT EXISTS idx_sub_weapon_code ON sub_weapon(code);
CREATE INDEX IF NOT EXISTS idx_special_weapon_code ON special_weapon(code);

-- -- 外键约束 (DEFERRABLE 方便批量导入)
-- ALTER TABLE main_weapon
--     ADD CONSTRAINT fk_main_weapon_sub_weapon
--         FOREIGN KEY (sub_weapon_code) REFERENCES sub_weapon(code)
--         ON UPDATE CASCADE ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
--     ADD CONSTRAINT fk_main_weapon_special_weapon
--         FOREIGN KEY (special_weapon_code) REFERENCES special_weapon(code)
--         ON UPDATE CASCADE ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

COMMENT ON TABLE main_weapon IS '主武器表';
COMMENT ON COLUMN main_weapon.code IS '武器代码(params.json中的key)';
COMMENT ON COLUMN main_weapon.special_point IS '特殊武器充能点数';
COMMENT ON COLUMN main_weapon.sub_weapon_code IS '副武器代码(sub_weapon.code)';
COMMENT ON COLUMN main_weapon.special_weapon_code IS '特殊武器代码(special_weapon.code)';
COMMENT ON COLUMN main_weapon.zh_name IS '中文名称';
COMMENT ON COLUMN main_weapon.weapon_class IS '武器类型(射击枪/滚筒等)';
COMMENT ON COLUMN main_weapon.distance_class IS '距离类型(近距离/中距离/长距离)';
COMMENT ON COLUMN main_weapon.params IS '其他参数(JSON格式)';

COMMENT ON TABLE sub_weapon IS '副武器表';
COMMENT ON COLUMN sub_weapon.code IS '副武器代码';
COMMENT ON COLUMN sub_weapon.ink_consume IS '墨水消耗量';
COMMENT ON COLUMN sub_weapon.zh_name IS '中文名称';
COMMENT ON COLUMN sub_weapon.params IS '其他参数(JSON格式)';

COMMENT ON TABLE special_weapon IS '特殊武器表';
COMMENT ON COLUMN special_weapon.code IS '特殊武器代码';
COMMENT ON COLUMN special_weapon.zh_name IS '中文名称';
COMMENT ON COLUMN special_weapon.params IS '参数(JSON格式)';

-- 装备能力表
CREATE TABLE IF NOT EXISTS skill (
    id SERIAL PRIMARY KEY,
    code VARCHAR(64) NOT NULL UNIQUE,
    zh_name VARCHAR(128) ,
    zh_desc TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_skill_code ON skill(code);
CREATE INDEX IF NOT EXISTS idx_skill_zh_name ON skill(zh_name);

COMMENT ON TABLE skill IS '装备能力表';
COMMENT ON COLUMN skill.code IS '能力代码 (如 Action_Up)';
COMMENT ON COLUMN skill.zh_name IS '中文名称';
COMMENT ON COLUMN skill.zh_desc IS '中文描述';

-- 地图表
CREATE TABLE IF NOT EXISTS stage (
    id SERIAL PRIMARY KEY,
    vs_stage_id INTEGER UNIQUE,
    code VARCHAR(64) NOT NULL UNIQUE,
    zh_name VARCHAR(128),
    stage_type VARCHAR(10) CHECK (stage_type IN ('VS', 'Coop')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stage_code ON stage(code);
CREATE INDEX IF NOT EXISTS idx_stage_vs_stage_id ON stage(vs_stage_id);
CREATE INDEX IF NOT EXISTS idx_stage_stage_type ON stage(stage_type);

COMMENT ON TABLE stage IS '地图表';
COMMENT ON COLUMN stage.vs_stage_id IS 'VS模式地图ID (Coop地图为NULL)';
COMMENT ON COLUMN stage.code IS '地图代码 (如 AutoWalk)';
COMMENT ON COLUMN stage.zh_name IS '中文名称';
COMMENT ON COLUMN stage.stage_type IS '地图类型 (VS/Coop)';
