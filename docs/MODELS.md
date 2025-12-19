# 数据模型文档

> SplatNet3 API 响应数据的解析模型

## 概述

本项目使用 Python dataclass 对 SplatNet3 GraphQL API 和 NS API 的响应数据进行结构化解析。所有模型都提供 `from_dict()` 类方法用于从 JSON 数据创建实例。

## 模型分类

### 基础模型

| 模型 | 说明 |
|------|------|
| `Image` | 图片（url, width, height） |
| `NamedEntity` | 带 id/name 的通用实体 |
| `DecodedId` | Base64 ID 解码工具 |

### 武器模型

| 模型 | 说明 |
|------|------|
| `Weapon` | 武器（含副武器、特殊武器） |
| `SubWeapon` | 副武器 |
| `SpecialWeapon` | 特殊武器 |

### 装备模型

| 模型 | 说明 |
|------|------|
| `Brand` | 装备品牌（含常用技能加成） |
| `GearPower` | 装备技能 |
| `Gear` | 装备（简化版） |
| `GearDetail` | 详细装备信息（含品牌） |

### 对战模型

| 模型 | 说明 |
|------|------|
| `VsMode` | 对战模式（BANKARA/REGULAR/XMATCH 等） |
| `VsRule` | 对战规则（塔楼/区域/鱼虎/蛤蜊） |
| `VsStage` | 对战地图 |
| `BattlePlayer` | 对战玩家（简化版） |
| `BankaraMatch` | 蛮颓对战信息 |
| `BattleHistoryDetail` | 对战详情（简化版） |
| `BattleSummary` | 对战统计摘要 |
| `BattleHistories` | 对战历史列表 |

### 对战详情模型

| 模型 | 说明 |
|------|------|
| `VsPlayerDetail` | 对战玩家详情（含完整装备信息） |
| `TeamColor` | 队伍颜色（RGBA） |
| `VsTeamResult` | 对战队伍结果 |
| `VsTeam` | 对战队伍（含玩家列表） |
| `VsHistoryDetailFull` | 完整对战详情 |

### 打工模型

| 模型 | 说明 |
|------|------|
| `CoopGrade` | 打工等级 |
| `CoopStage` | 打工地图 |
| `CoopScale` | 打工鳞片 |
| `CoopPointCard` | 打工积分卡 |
| `CoopHistoryDetail` | 打工详情（简化版） |
| `CoopResult` | 打工结果 |

### 打工详情模型

| 模型 | 说明 |
|------|------|
| `CoopUniform` | 打工制服 |
| `CoopWeapon` | 打工武器 |
| `CoopSpecialWeapon` | 打工特殊武器 |
| `CoopPlayerDetail` | 打工玩家信息 |
| `CoopPlayerResult` | 打工玩家战绩 |
| `CoopEnemy` | 打工敌人 |
| `CoopEnemyResult` | 敌人击杀战绩 |
| `CoopBossResult` | 头目战绩 |
| `CoopWave` | 波次信息 |
| `CoopHistoryDetailFull` | 完整打工详情 |

### 好友模型

| 模型 | 说明 |
|------|------|
| `Friend` | 好友 |
| `FriendList` | 好友列表 |

### 玩家模型

| 模型 | 说明 |
|------|------|
| `Badge` | 徽章 |
| `Nameplate` | 铭牌 |
| `NameplateBackground` | 铭牌背景 |
| `CurrentPlayer` | 当前玩家 |

### 主页模型

| 模型 | 说明 |
|------|------|
| `Banner` | 轮播图 |
| `HomeData` | 主页数据 |

### 记录模型

| 模型 | 说明 |
|------|------|
| `StageStats` | 地图统计数据 |
| `StageRecord` | 地图记录 |
| `StageRecords` | 地图记录列表 |
| `WeaponStats` | 武器统计数据 |
| `WeaponRecord` | 武器记录 |
| `WeaponRecords` | 武器记录列表 |

### NS API 模型

| 模型 | 说明 |
|------|------|
| `NSGame` | NS 游戏信息 |
| `NSPresence` | NS 在线状态 |
| `NSFriend` | NS 好友 |
| `NSFriendList` | NS 好友列表 |
| `NSMyself` | NS 个人信息 |

### 历史记录模型

| 模型 | 说明 |
|------|------|
| `XMatchMax` | X 赛最高分 |
| `MatchPlayHistory` | 比赛游玩历史 |
| `PlayHistory` | 游戏历史 |
| `HistorySummary` | 历史总结 |

---

## 核心模型详解

### VsHistoryDetailFull（完整对战详情）

```python
@dataclass
class VsHistoryDetailFull:
    id: str
    vs_mode: Optional[VsMode]           # 对战模式
    vs_rule: Optional[VsRule]           # 对战规则
    vs_stage: Optional[VsStage]         # 对战地图
    judgement: Optional[str]            # 结果: WIN/LOSE/DRAW
    knockout: Optional[str]             # KO 状态
    player: Optional[VsPlayerDetail]    # 当前玩家详情
    my_team: Optional[VsTeam]           # 我方队伍
    other_teams: List[VsTeam]           # 敌方队伍
    udemae: Optional[str]               # 段位
    bankara_match: Optional[BankaraMatch]
    played_time: Optional[str]          # 游玩时间
    duration: Optional[int]             # 持续时间(秒)
```

**模型关系：**
```
VsHistoryDetailFull
├── player: VsPlayerDetail
│   ├── nameplate: Nameplate
│   ├── weapon: Weapon
│   ├── head_gear: GearDetail
│   │   ├── primary_gear_power: GearPower
│   │   ├── additional_gear_powers: List[GearPower]
│   │   └── brand: Brand
│   ├── clothing_gear: GearDetail
│   └── shoes_gear: GearDetail
├── my_team: VsTeam
│   ├── color: TeamColor
│   ├── result: VsTeamResult
│   └── players: List[VsPlayerDetail]
└── other_teams: List[VsTeam]
```

### VsPlayerDetail（对战玩家详情）

```python
@dataclass
class VsPlayerDetail:
    id: str
    name: str
    name_id: str
    byname: Optional[str]               # 称号
    species: Optional[str]              # INKLING/OCTOLING
    nameplate: Optional[Nameplate]      # 铭牌
    weapon: Optional[Weapon]            # 武器
    head_gear: Optional[GearDetail]     # 头部装备
    clothing_gear: Optional[GearDetail] # 服装
    shoes_gear: Optional[GearDetail]    # 鞋子
    paint: int                          # 涂色点数
    is_myself: bool                     # 是否是自己
```

### CoopHistoryDetailFull（完整打工详情）

```python
@dataclass
class CoopHistoryDetailFull:
    id: str
    coop_stage: Optional[CoopStage]     # 打工地图
    after_grade: Optional[CoopGrade]    # 结算后等级
    after_grade_point: Optional[int]    # 结算后分数
    grade_point_diff: Optional[str]     # 分数变化: UP/DOWN/KEEP
    danger_rate: Optional[float]        # 危险度
    result_wave: int                    # 结果波次 (0=通关)
    played_time: Optional[str]          # 游玩时间
    my_result: Optional[CoopPlayerResult]       # 自己的战绩
    member_results: List[CoopPlayerResult]      # 队友战绩
    boss_result: Optional[CoopBossResult]       # 头目战绩
    boss_results: List[CoopBossResult]          # 所有头目战绩
    enemy_results: List[CoopEnemyResult]        # 敌人战绩
    wave_results: List[CoopWave]                # 波次信息
    weapons: List[CoopWeapon]                   # 本局武器
```

**模型关系：**
```
CoopHistoryDetailFull
├── my_result: CoopPlayerResult
│   ├── player: CoopPlayerDetail
│   │   ├── nameplate: Nameplate
│   │   └── uniform: CoopUniform
│   ├── weapons: List[CoopWeapon]
│   └── special_weapon: CoopSpecialWeapon
├── member_results: List[CoopPlayerResult]
├── enemy_results: List[CoopEnemyResult]
│   └── enemy: CoopEnemy
├── boss_results: List[CoopBossResult]
│   └── boss: CoopEnemy
└── wave_results: List[CoopWave]
```

### CoopPlayerResult（打工玩家战绩）

```python
@dataclass
class CoopPlayerResult:
    player: Optional[CoopPlayerDetail]  # 玩家信息
    weapons: List[CoopWeapon]           # 使用的武器（4个）
    special_weapon: Optional[CoopSpecialWeapon]  # 特殊武器
    defeat_enemy_count: int             # 击杀敌人数
    deliver_count: int                  # 收集鲑鱼卵数
    golden_assist_count: int            # 金鲑鱼卵助攻数
    golden_deliver_count: int           # 金鲑鱼卵收集数
    rescue_count: int                   # 救援队友次数
    rescued_count: int                  # 被救援次数
```

---

## 使用示例

### 解析对战详情

```python
import json
from src import VsHistoryDetailFull

with open("battle_detail.json") as f:
    data = json.load(f)

battle = VsHistoryDetailFull.from_dict(data)

# 访问数据
print(f"模式: {battle.vs_mode.mode}")
print(f"规则: {battle.vs_rule.name}")
print(f"结果: {battle.judgement}")
print(f"是否胜利: {battle.is_win}")

# 玩家装备
player = battle.player
print(f"玩家: {player.full_name}")
print(f"头部: {player.head_gear.name} (品牌: {player.head_gear.brand.name})")
print(f"涂色: {player.paint}")

# 队伍信息
print(f"我方人数: {len(battle.my_team.players)}")
for p in battle.my_team.players:
    print(f"  - {p.name}: {p.weapon.name}")
```

### 解析打工详情

```python
import json
from src import CoopHistoryDetailFull

with open("coop_detail.json") as f:
    data = json.load(f)

coop = CoopHistoryDetailFull.from_dict(data)

# 访问数据
print(f"地图: {coop.coop_stage.name}")
print(f"等级: {coop.after_grade.name}")
print(f"危险度: {coop.danger_rate}")
print(f"是否通关: {coop.is_clear}")

# 自己的战绩
my = coop.my_result
print(f"玩家: {my.player.name}")
print(f"制服: {my.player.uniform.name}")
print(f"金蛋: {my.golden_deliver_count} (助攻: {my.golden_assist_count})")
print(f"救援: {my.rescue_count} / 被救: {my.rescued_count}")

# 所有玩家
for p in coop.all_players:
    print(f"  - {p.player.name}: 金蛋 {p.golden_deliver_count}")
```

### 解码 Base64 ID

```python
from src import DecodedId

# 解码对战 ID
battle_id = "VnNIaXN0b3J5RGV0YWlsLXUtcXpnNmRpbzdkNXRuZmZyamFubW06UkVDRU5UOjIwMjUxMjExVDE0MzEwMV82NmJjZWFjMC01MzUzLTRlMDEtOWNiMC04ZTg0YzQ2NmIxM2E="
decoded = DecodedId.decode(battle_id)

print(f"原始: {decoded.raw}")
print(f"解码: {decoded.decoded}")
print(f"类型: {decoded.type_prefix}")  # VsHistoryDetail
print(f"时间戳: {decoded.timestamp}")  # 20251211T143101
```

---

## API 方法与模型对应

| API 方法 | 返回模型 |
|----------|----------|
| `get_home()` | `HomeData` |
| `get_friends()` | `FriendList` |
| `get_recent_battles()` | `BattleHistories` |
| `get_bankara_battles()` | `BattleHistories` |
| `get_x_battles()` | `BattleHistories` |
| `get_coops()` | `CoopResult` |
| `get_battle_detail(id)` | `VsHistoryDetailFull` |
| `get_coop_detail(id)` | `CoopHistoryDetailFull` |
| `get_stage_records()` | `StageRecords` |
| `get_weapon_records()` | `WeaponRecords` |
| `get_history_summary()` | `HistorySummary` |
| `get_app_ns_friend_list()` | `NSFriendList` |
| `get_app_ns_myself()` | `NSMyself` |
