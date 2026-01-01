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
    session_expired INTEGER NOT NULL DEFAULT 0 CHECK (session_expired IN (0, 1)),
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
    weapon_power REAL,                      -- 武器力（来自 bankaraMatch.weaponPower）
    bankara_power REAL,                     -- 真格战力（来自 bankaraMatch.bankaraPower.power）
    my_league_power REAL,                   -- 活动赛力量（来自 leagueMatch.myLeaguePower）
    league_match_event_name TEXT,           -- 活动赛事件名称（来自 leagueMatch.leagueMatchEvent.name）

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

-- ===========================================
-- 打工详情主表
-- ===========================================
CREATE TABLE IF NOT EXISTS coop_detail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,               -- 归属用户
    splatoon_id TEXT NOT NULL,              -- 从base64解密的玩家ID (u-xxx)
    played_time TEXT NOT NULL,              -- 游戏时间 (ISO8601)
    rule TEXT NOT NULL,                     -- 规则 (REGULAR/BIG_RUN/TEAM_CONTEST)
    danger_rate REAL,                       -- 危险度
    result_wave INTEGER,                    -- 结果波次 (0=通关)
    smell_meter INTEGER,                    -- 臭味计
    stage_id TEXT,                          -- 场地ID (base64解密后)
    stage_name TEXT,                        -- 场地名称
    after_grade_id TEXT,                    -- 段位ID (base64解密后)
    after_grade_name TEXT,                  -- 段位名称
    after_grade_point INTEGER,              -- 段位点数
    boss_id TEXT,                           -- Extra Wave Boss ID
    boss_name TEXT,                         -- Extra Wave Boss 名称
    boss_defeated INTEGER DEFAULT 0,        -- 是否击败Boss (0/1)
    scale_gold INTEGER DEFAULT 0,           -- 金鳞片
    scale_silver INTEGER DEFAULT 0,         -- 银鳞片
    scale_bronze INTEGER DEFAULT 0,         -- 铜鳞片
    job_point INTEGER,                      -- 打工点数
    job_score INTEGER,                      -- 打工分数
    job_rate REAL,                          -- 打工倍率
    job_bonus INTEGER,                      -- 打工奖励
    images JSON,                            -- 图片 {场地名:url, Boss名:url}
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, splatoon_id, played_time)
);

CREATE INDEX IF NOT EXISTS idx_coop_detail_user_time ON coop_detail(user_id, played_time DESC);
CREATE INDEX IF NOT EXISTS idx_coop_detail_rule ON coop_detail(rule);
CREATE INDEX IF NOT EXISTS idx_coop_detail_stage ON coop_detail(stage_id);
CREATE INDEX IF NOT EXISTS idx_coop_detail_splatoon_id ON coop_detail(splatoon_id);

-- ===========================================
-- 打工玩家表
-- ===========================================
CREATE TABLE IF NOT EXISTS coop_player (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coop_id INTEGER NOT NULL,               -- 关联 coop_detail.id
    player_order INTEGER NOT NULL,          -- 玩家顺序 (0=自己)
    is_myself INTEGER DEFAULT 0,            -- 是否是自己 (0/1)
    player_id TEXT,                         -- 玩家ID (base64解密后)
    name TEXT NOT NULL,                     -- 玩家名称
    name_id TEXT,                           -- 玩家名称ID
    byname TEXT,                            -- 称号
    species TEXT,                           -- 种族 (INKLING/OCTOLING)
    uniform_id TEXT,                        -- 工作服ID (base64解密后)
    uniform_name TEXT,                      -- 工作服名称
    special_weapon_id INTEGER,              -- 大招ID (weaponId字段)
    special_weapon_name TEXT,               -- 大招名称
    weapons JSON,                           -- 武器ID列表 (base64解密后)
    weapon_names JSON,                      -- 武器名称列表
    defeat_enemy_count INTEGER DEFAULT 0,   -- 击杀鲑鱼数
    deliver_count INTEGER DEFAULT 0,        -- 运蛋数(红蛋)
    golden_assist_count INTEGER DEFAULT 0,  -- 金蛋助攻数
    golden_deliver_count INTEGER DEFAULT 0, -- 金蛋入筐数
    rescue_count INTEGER DEFAULT 0,         -- 救人次数
    rescued_count INTEGER DEFAULT 0,        -- 被救次数
    images JSON,                            -- 图片 {武器名:url, 大招名:url, 工作服名:url}
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coop_id, player_order)
);

CREATE INDEX IF NOT EXISTS idx_coop_player_coop ON coop_player(coop_id);
CREATE INDEX IF NOT EXISTS idx_coop_player_myself ON coop_player(coop_id) WHERE is_myself = 1;

-- ===========================================
-- 打工波次表
-- ===========================================
CREATE TABLE IF NOT EXISTS coop_wave (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coop_id INTEGER NOT NULL,               -- 关联 coop_detail.id
    wave_number INTEGER NOT NULL,           -- 波次 (1-4, 4=Extra Wave)
    water_level INTEGER,                    -- 水位 (0=低, 1=中, 2=高)
    event_id TEXT,                          -- 特殊事件ID (base64解密后)
    event_name TEXT,                        -- 特殊事件名称 (狂潮/走私鱼来袭/...)
    deliver_norm INTEGER,                   -- 目标金蛋数
    golden_pop_count INTEGER,               -- 金蛋出现数
    team_deliver_count INTEGER,             -- 团队实际交付数
    special_weapons JSON,                   -- 使用的大招ID列表
    special_weapon_names JSON,              -- 使用的大招名称列表
    images JSON,                            -- 图片 {事件名:url, 大招名:url}
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coop_id, wave_number)
);

CREATE INDEX IF NOT EXISTS idx_coop_wave_coop ON coop_wave(coop_id);
CREATE INDEX IF NOT EXISTS idx_coop_wave_event ON coop_wave(event_id);

-- ===========================================
-- 打工敌人统计表
-- ===========================================
CREATE TABLE IF NOT EXISTS coop_enemy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coop_id INTEGER NOT NULL,               -- 关联 coop_detail.id
    enemy_id TEXT NOT NULL,                 -- 敌人ID (base64解密后)
    enemy_name TEXT,                        -- 敌人名称
    defeat_count INTEGER DEFAULT 0,         -- 我击杀数
    team_defeat_count INTEGER DEFAULT 0,    -- 团队击杀数
    pop_count INTEGER DEFAULT 0,            -- 出现数
    images JSON,                            -- 图片 {敌人名:url}
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coop_id, enemy_id)
);

CREATE INDEX IF NOT EXISTS idx_coop_enemy_coop ON coop_enemy(coop_id);
CREATE INDEX IF NOT EXISTS idx_coop_enemy_enemy ON coop_enemy(enemy_id);

-- ===========================================
-- 打工Boss结果表
-- ===========================================
CREATE TABLE IF NOT EXISTS coop_boss (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coop_id INTEGER NOT NULL,               -- 关联 coop_detail.id
    boss_id TEXT NOT NULL,                  -- Boss ID (base64解密后)
    boss_name TEXT,                         -- Boss名称 (横纲/辰龙/巨颚)
    has_defeat_boss INTEGER DEFAULT 0,      -- 是否击败 (0/1)
    images JSON,                            -- 图片 {Boss名:url}
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coop_id, boss_id)
);

CREATE INDEX IF NOT EXISTS idx_coop_boss_coop ON coop_boss(coop_id);
CREATE INDEX IF NOT EXISTS idx_coop_boss_boss ON coop_boss(boss_id);
