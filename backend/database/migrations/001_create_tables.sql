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

-- 用户武器战绩表
CREATE TABLE IF NOT EXISTS user_weapon_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    main_weapon_id INTEGER NOT NULL,
    main_weapon_name TEXT NOT NULL,
    last_used_time TEXT,
    level INTEGER NOT NULL DEFAULT 0,
    exp_to_level_up INTEGER NOT NULL DEFAULT 0,
    win INTEGER NOT NULL DEFAULT 0,
    vibes REAL NOT NULL DEFAULT 0.0,
    paint INTEGER NOT NULL DEFAULT 0,
    current_weapon_power REAL,
    max_weapon_power REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, main_weapon_id)
);

CREATE INDEX IF NOT EXISTS idx_user_weapon_record_user_id ON user_weapon_record(user_id);
CREATE INDEX IF NOT EXISTS idx_user_weapon_record_main_weapon_id ON user_weapon_record(main_weapon_id);

-- ===========================================
-- 对战详情主表
-- ===========================================
CREATE TABLE IF NOT EXISTS battle_detail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,               -- 归属用户
    splatoon_id TEXT NOT NULL,              -- 从解码ID提取的用户标识（如 u-qzg6dio7d5tnffrjanmm）
    base64_decode_id TEXT NOT NULL,         -- Base64 解码后的完整 ID（冗余存储）

    -- 对战基础信息
    played_time TEXT NOT NULL,              -- ISO8601 时间戳
    duration INTEGER NOT NULL,              -- 时长(秒)
    vs_mode TEXT NOT NULL,                  -- BANKARA/REGULAR/X_MATCH/LEAGUE/FEST/PRIVATE
    vs_rule TEXT NOT NULL,                  -- AREA/LOFT/GOAL/CLAM/TURF_WAR
    vs_stage_id INTEGER,                    -- 对应 stage.vs_stage_id
    judgement TEXT NOT NULL,                -- WIN/LOSE/EXEMPTED_LOSE/DEEMED_LOSE
    knockout TEXT,                          -- WIN/LOSE/NEITHER

    -- 模式特有字段（常用值独立列）
    bankara_mode TEXT,                      -- OPEN/CHALLENGE
    udemae TEXT,                            -- 段位 S+0, A-（从列表接口获取）
    x_power REAL,                           -- X赛战力（从列表接口获取）
    fest_power REAL,                        -- 祭典战力
    league_match_event_id TEXT,             -- 联赛事件ID

    -- 扩展数据
    mode_extra JSON,
    awards JSON,                            -- 徽章数组

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, splatoon_id, played_time)
);

CREATE INDEX IF NOT EXISTS idx_battle_detail_user_time ON battle_detail(user_id, played_time DESC);
CREATE INDEX IF NOT EXISTS idx_battle_detail_mode_rule ON battle_detail(vs_mode, vs_rule);
CREATE INDEX IF NOT EXISTS idx_battle_detail_stage ON battle_detail(vs_stage_id);
CREATE INDEX IF NOT EXISTS idx_battle_detail_judgement ON battle_detail(judgement);
CREATE INDEX IF NOT EXISTS idx_battle_detail_splatoon_id ON battle_detail(splatoon_id);
CREATE INDEX IF NOT EXISTS idx_battle_detail_decode_id ON battle_detail(base64_decode_id);

-- ===========================================
-- 队伍表
-- ===========================================
CREATE TABLE IF NOT EXISTS battle_team (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id INTEGER NOT NULL,             -- 对应 battle_detail.id
    team_role TEXT NOT NULL,                -- MY/OPPONENT/OTHER (Tricolor第三队)
    team_order INTEGER NOT NULL DEFAULT 0,  -- 多队时的排序

    -- 队伍结果
    paint_ratio REAL,
    score INTEGER,
    noroshi INTEGER,                        -- 信号塔
    judgement TEXT,                         -- 队伍判定 WIN/LOSE

    -- 祭典相关
    fest_team_name TEXT,
    fest_uniform_name TEXT,
    fest_uniform_bonus_rate REAL,
    fest_streak_win_count INTEGER,
    tricolor_role TEXT,                     -- ATTACK/DEFENSE

    -- 颜色
    color JSON,                             -- { "a": 1, "r": 0.5, "g": 0.2, "b": 0.8 }

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(battle_id, team_role, team_order)
);

CREATE INDEX IF NOT EXISTS idx_battle_team_battle ON battle_team(battle_id);

-- ===========================================
-- 玩家表
-- ===========================================
CREATE TABLE IF NOT EXISTS battle_player (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id INTEGER NOT NULL,             -- 对应 battle_detail.id
    team_id INTEGER NOT NULL,               -- 对应 battle_team.id
    player_order INTEGER NOT NULL,          -- 队内顺序

    -- 玩家身份
    player_id TEXT,                         -- 官方玩家ID（Base64解码后）
    name TEXT NOT NULL,
    name_id TEXT,                           -- #1234
    byname TEXT,                            -- 称号
    species TEXT,                           -- INKLING/OCTOLING
    is_myself INTEGER NOT NULL DEFAULT 0,

    -- 武器
    weapon_id INTEGER,                      -- 对应 main_weapon.id

    -- 装备技能（主技能列化，副技能JSON）
    head_main_skill TEXT,
    head_additional_skills JSON,
    clothing_main_skill TEXT,
    clothing_additional_skills JSON,
    shoes_main_skill TEXT,
    shoes_additional_skills JSON,

    -- 技能图片（{技能名: 图片URL} 格式）
    head_skills_images JSON,                -- {"主技能": "url", "副技能1": "url", ...}
    clothing_skills_images JSON,
    shoes_skills_images JSON,

    -- 战绩
    paint INTEGER DEFAULT 0,
    kill_count INTEGER DEFAULT 0,
    assist_count INTEGER DEFAULT 0,
    death_count INTEGER DEFAULT 0,
    special_count INTEGER DEFAULT 0,
    noroshi_try INTEGER DEFAULT 0,

    -- 特殊状态
    crown INTEGER DEFAULT 0,                -- X赛王冠
    fest_dragon_cert TEXT,                  -- 祭典龙认证

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(battle_id, team_id, player_order)
);

CREATE INDEX IF NOT EXISTS idx_battle_player_battle ON battle_player(battle_id);
CREATE INDEX IF NOT EXISTS idx_battle_player_weapon ON battle_player(weapon_id);
CREATE INDEX IF NOT EXISTS idx_battle_player_myself ON battle_player(battle_id) WHERE is_myself = 1;

-- ===========================================
-- 徽章表（便于统计分析）
-- ===========================================
CREATE TABLE IF NOT EXISTS battle_award (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id INTEGER NOT NULL,             -- 对应 battle_detail.id
    user_id INTEGER NOT NULL,
    award_name TEXT NOT NULL,
    award_rank TEXT,                        -- GOLD/SILVER

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(battle_id, award_name)
);

CREATE INDEX IF NOT EXISTS idx_battle_award_user ON battle_award(user_id, award_name);
CREATE INDEX IF NOT EXISTS idx_battle_award_battle ON battle_award(battle_id);
