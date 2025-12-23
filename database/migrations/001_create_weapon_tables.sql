-- Splatoon3 武器数据表
-- 执行方式: psql -U postgres -d splatoon3 -f 001_create_weapon_tables.sql

-- 副武器表 (先创建，被主武器表引用)
CREATE TABLE IF NOT EXISTS sub_weapons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    ink_consume DECIMAL(5,4),
    zh_name VARCHAR(100),
    params JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 特殊武器表 (先创建，被主武器表引用)
CREATE TABLE IF NOT EXISTS special_weapons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    zh_name VARCHAR(100),
    params JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 主武器表
CREATE TABLE IF NOT EXISTS main_weapons (
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
CREATE INDEX IF NOT EXISTS idx_main_weapons_code ON main_weapons(code);
CREATE INDEX IF NOT EXISTS idx_main_weapons_sub_weapon_code ON main_weapons(sub_weapon_code);
CREATE INDEX IF NOT EXISTS idx_main_weapons_special_weapon_code ON main_weapons(special_weapon_code);
CREATE INDEX IF NOT EXISTS idx_main_weapons_weapon_class ON main_weapons(weapon_class);
CREATE INDEX IF NOT EXISTS idx_sub_weapons_code ON sub_weapons(code);
CREATE INDEX IF NOT EXISTS idx_special_weapons_code ON special_weapons(code);

-- -- 外键约束 (DEFERRABLE 方便批量导入)
-- ALTER TABLE main_weapons
--     ADD CONSTRAINT fk_main_weapons_sub_weapon
--         FOREIGN KEY (sub_weapon_code) REFERENCES sub_weapons(code)
--         ON UPDATE CASCADE ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
--     ADD CONSTRAINT fk_main_weapons_special_weapon
--         FOREIGN KEY (special_weapon_code) REFERENCES special_weapons(code)
--         ON UPDATE CASCADE ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

COMMENT ON TABLE main_weapons IS '主武器表';
COMMENT ON COLUMN main_weapons.code IS '武器代码(params.json中的key)';
COMMENT ON COLUMN main_weapons.special_point IS '特殊武器充能点数';
COMMENT ON COLUMN main_weapons.sub_weapon_code IS '副武器代码(sub_weapons.code)';
COMMENT ON COLUMN main_weapons.special_weapon_code IS '特殊武器代码(special_weapons.code)';
COMMENT ON COLUMN main_weapons.zh_name IS '中文名称';
COMMENT ON COLUMN main_weapons.weapon_class IS '武器类型(射击枪/滚筒等)';
COMMENT ON COLUMN main_weapons.distance_class IS '距离类型(近距离/中距离/长距离)';
COMMENT ON COLUMN main_weapons.params IS '其他参数(JSON格式)';

COMMENT ON TABLE sub_weapons IS '副武器表';
COMMENT ON COLUMN sub_weapons.code IS '副武器代码';
COMMENT ON COLUMN sub_weapons.ink_consume IS '墨水消耗量';
COMMENT ON COLUMN sub_weapons.zh_name IS '中文名称';
COMMENT ON COLUMN sub_weapons.params IS '其他参数(JSON格式)';

COMMENT ON TABLE special_weapons IS '特殊武器表';
COMMENT ON COLUMN special_weapons.code IS '特殊武器代码';
COMMENT ON COLUMN special_weapons.zh_name IS '中文名称';
COMMENT ON COLUMN special_weapons.params IS '参数(JSON格式)';
