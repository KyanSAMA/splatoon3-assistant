# Data models for Splatoon3 API responses
"""数据模型定义 - 基于 SplatNet3 GraphQL API 响应结构"""

from dataclasses import dataclass, field
from typing import Optional, List, Any
from datetime import datetime
import base64


# ============================================================
# 基础模型
# ============================================================

@dataclass
class Image:
    """图片"""
    url: str
    width: Optional[int] = None
    height: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["Image"]:
        if not data:
            return None
        return cls(
            url=data.get("url", ""),
            width=data.get("width"),
            height=data.get("height"),
        )


@dataclass
class NamedEntity:
    """带 id/name 的通用实体"""
    id: str
    name: str

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["NamedEntity"]:
        if not data:
            return None
        return cls(id=data.get("id", ""), name=data.get("name", ""))


# ============================================================
# ID 解码工具
# ============================================================

@dataclass
class DecodedId:
    """解码后的 Base64 ID"""
    raw: str
    decoded: str
    parts: List[str]

    @classmethod
    def decode(cls, encoded_id: str) -> "DecodedId":
        try:
            decoded = base64.b64decode(encoded_id).decode("utf-8")
            parts = decoded.split(":")
        except Exception:
            decoded = encoded_id
            parts = [encoded_id]
        return cls(raw=encoded_id, decoded=decoded, parts=parts)

    @property
    def type_prefix(self) -> str:
        """类型前缀，如 VsPlayer, CoopHistoryDetail"""
        return self.parts[0].split("-")[0] if self.parts else ""

    @property
    def user_id(self) -> Optional[str]:
        """用户 ID"""
        if len(self.parts) > 0 and "-" in self.parts[0]:
            return self.parts[0].split("-", 1)[1]
        return None

    @property
    def timestamp(self) -> Optional[str]:
        """时间戳部分"""
        for part in self.parts:
            if part.startswith("20") and "T" in part:
                return part.split("_")[0]
        return None


# ============================================================
# 武器模型
# ============================================================

@dataclass
class SubWeapon:
    """副武器"""
    id: str
    name: str
    image: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["SubWeapon"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            image=Image.from_dict(data.get("image")),
        )


@dataclass
class SpecialWeapon:
    """特殊武器"""
    id: str
    name: str
    image: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["SpecialWeapon"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            image=Image.from_dict(data.get("image")),
        )


@dataclass
class Weapon:
    """武器"""
    id: str
    name: str
    image: Optional[Image] = None
    sub_weapon: Optional[SubWeapon] = None
    special_weapon: Optional[SpecialWeapon] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["Weapon"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            image=Image.from_dict(data.get("image")),
            sub_weapon=SubWeapon.from_dict(data.get("subWeapon")),
            special_weapon=SpecialWeapon.from_dict(data.get("specialWeapon")),
        )


# ============================================================
# 品牌模型
# ============================================================

@dataclass
class Brand:
    """装备品牌"""
    id: str
    name: str
    image: Optional[Image] = None
    usual_gear_power: Optional["GearPower"] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["Brand"]:
        if not data:
            return None
        usual = data.get("usualGearPower") or {}
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            image=Image.from_dict(data.get("image")),
            usual_gear_power=GearPower.from_dict(usual) if usual else None,
        )


# ============================================================
# 装备模型
# ============================================================

@dataclass
class GearPower:
    """装备能力"""
    name: str
    image: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["GearPower"]:
        if not data:
            return None
        return cls(
            name=data.get("name", ""),
            image=Image.from_dict(data.get("image")),
        )


@dataclass
class Gear:
    """装备"""
    name: str
    image: Optional[Image] = None
    primary_gear_power: Optional[GearPower] = None
    additional_gear_powers: List[GearPower] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["Gear"]:
        if not data:
            return None
        additional = [
            GearPower.from_dict(p)
            for p in data.get("additionalGearPowers", [])
            if p
        ]
        return cls(
            name=data.get("name", ""),
            image=Image.from_dict(data.get("image")),
            primary_gear_power=GearPower.from_dict(data.get("primaryGearPower")),
            additional_gear_powers=[p for p in additional if p],
        )


@dataclass
class GearDetail:
    """详细装备信息（含品牌）"""
    name: str
    image: Optional[Image] = None
    original_image: Optional[Image] = None
    primary_gear_power: Optional[GearPower] = None
    additional_gear_powers: List[GearPower] = field(default_factory=list)
    brand: Optional[Brand] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["GearDetail"]:
        if not data:
            return None
        additional = [
            GearPower.from_dict(p)
            for p in data.get("additionalGearPowers") or []
            if p
        ]
        return cls(
            name=data.get("name", ""),
            image=Image.from_dict(data.get("image")),
            original_image=Image.from_dict(data.get("originalImage")),
            primary_gear_power=GearPower.from_dict(data.get("primaryGearPower")),
            additional_gear_powers=[p for p in additional if p],
            brand=Brand.from_dict(data.get("brand")),
        )


# ============================================================
# 对战模型
# ============================================================

@dataclass
class VsMode:
    """对战模式"""
    id: str
    mode: str  # BANKARA, REGULAR, XMATCH, PRIVATE, FEST
    name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["VsMode"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            mode=data.get("mode", ""),
            name=data.get("name"),
        )


@dataclass
class VsRule:
    """对战规则"""
    id: str
    name: str  # 真格塔楼、真格区域、真格鱼虎、真格蛤蜊

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["VsRule"]:
        if not data:
            return None
        return cls(id=data.get("id", ""), name=data.get("name", ""))


@dataclass
class VsStage:
    """对战地图"""
    id: str
    name: str
    image: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["VsStage"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            image=Image.from_dict(data.get("image")),
        )


@dataclass
class TeamResult:
    """队伍结果"""
    paint_point: Optional[int] = None
    score: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["TeamResult"]:
        if not data:
            return None
        result = data.get("result", {})
        return cls(
            paint_point=result.get("paintPoint") if result else None,
            score=result.get("score") if result else None,
        )


@dataclass
class BattlePlayer:
    """对战玩家"""
    id: str
    weapon: Optional[Weapon] = None
    fest_grade: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["BattlePlayer"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            weapon=Weapon.from_dict(data.get("weapon")),
            fest_grade=data.get("festGrade"),
        )

    @property
    def decoded_id(self) -> DecodedId:
        return DecodedId.decode(self.id)


@dataclass
class BankaraMatch:
    """蛮颓对战信息"""
    earned_udemae_point: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["BankaraMatch"]:
        if not data:
            return None
        return cls(earned_udemae_point=data.get("earnedUdemaePoint"))


@dataclass
class BattleHistoryDetail:
    """对战详情"""
    id: str
    vs_mode: Optional[VsMode] = None
    vs_rule: Optional[VsRule] = None
    vs_stage: Optional[VsStage] = None
    judgement: Optional[str] = None  # WIN, LOSE, DRAW
    knockout: Optional[str] = None  # WIN, LOSE, NEITHER
    player: Optional[BattlePlayer] = None
    my_team: Optional[TeamResult] = None
    udemae: Optional[str] = None  # 段位
    bankara_match: Optional[BankaraMatch] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["BattleHistoryDetail"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            vs_mode=VsMode.from_dict(data.get("vsMode")),
            vs_rule=VsRule.from_dict(data.get("vsRule")),
            vs_stage=VsStage.from_dict(data.get("vsStage")),
            judgement=data.get("judgement"),
            knockout=data.get("knockout"),
            player=BattlePlayer.from_dict(data.get("player")),
            my_team=TeamResult.from_dict(data.get("myTeam")),
            udemae=data.get("udemae"),
            bankara_match=BankaraMatch.from_dict(data.get("bankaraMatch")),
        )

    @property
    def decoded_id(self) -> DecodedId:
        return DecodedId.decode(self.id)

    @property
    def is_win(self) -> bool:
        return self.judgement == "WIN"


@dataclass
class BattleSummary:
    """对战统计摘要"""
    win: int = 0
    lose: int = 0
    kill_average: float = 0.0
    death_average: float = 0.0
    assist_average: float = 0.0
    special_average: float = 0.0

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["BattleSummary"]:
        if not data:
            return None
        return cls(
            win=data.get("win", 0),
            lose=data.get("lose", 0),
            kill_average=data.get("killAverage", 0.0),
            death_average=data.get("deathAverage", 0.0),
            assist_average=data.get("assistAverage", 0.0),
            special_average=data.get("specialAverage", 0.0),
        )

    @property
    def total(self) -> int:
        return self.win + self.lose

    @property
    def win_rate(self) -> float:
        return self.win / self.total if self.total > 0 else 0.0


@dataclass
class BattleHistories:
    """对战历史列表"""
    summary: Optional[BattleSummary] = None
    battles: List[BattleHistoryDetail] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[dict], history_key: str = "latestBattleHistories") -> Optional["BattleHistories"]:
        if not data or "data" not in data:
            return None
        data_inner = data.get("data") or {}
        histories = data_inner.get(history_key) or {}
        battles = []
        history_groups = histories.get("historyGroups") or {}
        for group in history_groups.get("nodes") or []:
            history_details = group.get("historyDetails") or {}
            for detail in history_details.get("nodes") or []:
                battle = BattleHistoryDetail.from_dict(detail)
                if battle:
                    battles.append(battle)
        return cls(
            summary=BattleSummary.from_dict(histories.get("summary")),
            battles=battles,
        )


# ============================================================
# 打工模型
# ============================================================

@dataclass
class CoopGrade:
    """打工等级"""
    id: str
    name: str

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopGrade"]:
        if not data:
            return None
        return cls(id=data.get("id", ""), name=data.get("name", ""))


@dataclass
class CoopStage:
    """打工地图"""
    id: str
    name: str

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopStage"]:
        if not data:
            return None
        return cls(id=data.get("id", ""), name=data.get("name", ""))


@dataclass
class CoopScale:
    """打工鳞片"""
    gold: int = 0
    silver: int = 0
    bronze: int = 0

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopScale"]:
        if not data:
            return None
        return cls(
            gold=data.get("gold", 0),
            silver=data.get("silver", 0),
            bronze=data.get("bronze", 0),
        )


@dataclass
class CoopPointCard:
    """打工积分卡"""
    play_count: int = 0
    rescue_count: int = 0
    deliver_count: int = 0
    golden_deliver_count: int = 0
    defeat_boss_count: int = 0
    total_point: int = 0

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopPointCard"]:
        if not data:
            return None
        return cls(
            play_count=data.get("playCount", 0),
            rescue_count=data.get("rescueCount", 0),
            deliver_count=data.get("deliverCount", 0),
            golden_deliver_count=data.get("goldenDeliverCount", 0),
            defeat_boss_count=data.get("defeatBossCount", 0),
            total_point=data.get("totalPoint", 0),
        )


@dataclass
class CoopHistoryDetail:
    """打工详情"""
    id: str
    coop_stage: Optional[CoopStage] = None
    after_grade: Optional[CoopGrade] = None
    after_grade_point: Optional[int] = None
    grade_point_diff: Optional[str] = None  # UP, DOWN, KEEP
    danger_rate: Optional[float] = None
    result_wave: Optional[int] = None
    weapons: List[Weapon] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopHistoryDetail"]:
        if not data:
            return None
        weapons = [
            Weapon.from_dict(w)
            for w in data.get("weapons", [])
            if w
        ]
        return cls(
            id=data.get("id", ""),
            coop_stage=CoopStage.from_dict(data.get("coopStage")),
            after_grade=CoopGrade.from_dict(data.get("afterGrade")),
            after_grade_point=data.get("afterGradePoint"),
            grade_point_diff=data.get("gradePointDiff"),
            danger_rate=data.get("dangerRate"),
            result_wave=data.get("resultWave"),
            weapons=[w for w in weapons if w],
        )

    @property
    def decoded_id(self) -> DecodedId:
        return DecodedId.decode(self.id)

    @property
    def is_clear(self) -> bool:
        return self.result_wave == 0


@dataclass
class CoopResult:
    """打工结果"""
    regular_grade: Optional[CoopGrade] = None
    regular_grade_point: Optional[int] = None
    scale: Optional[CoopScale] = None
    point_card: Optional[CoopPointCard] = None
    details: List[CoopHistoryDetail] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopResult"]:
        if not data or "data" not in data:
            return None
        data_inner = data.get("data") or {}
        coop = data_inner.get("coopResult") or {}
        details = []
        history_groups = coop.get("historyGroups") or {}
        for group in history_groups.get("nodes") or []:
            history_details = group.get("historyDetails") or {}
            for detail in history_details.get("nodes") or []:
                d = CoopHistoryDetail.from_dict(detail)
                if d:
                    details.append(d)
        return cls(
            regular_grade=CoopGrade.from_dict(coop.get("regularGrade")),
            regular_grade_point=coop.get("regularGradePoint"),
            scale=CoopScale.from_dict(coop.get("scale")),
            point_card=CoopPointCard.from_dict(coop.get("pointCard")),
            details=details,
        )


# ============================================================
# 好友模型
# ============================================================

@dataclass
class Friend:
    """好友"""
    id: str
    nickname: str
    player_name: Optional[str] = None
    online_state: Optional[str] = None  # ONLINE, OFFLINE, VS_MODE_MATCHING, COOP_MODE_MATCHING
    user_icon: Optional[Image] = None
    vs_mode: Optional[VsMode] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["Friend"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            nickname=data.get("nickname", ""),
            player_name=data.get("playerName"),
            online_state=data.get("onlineState"),
            user_icon=Image.from_dict(data.get("userIcon")),
            vs_mode=VsMode.from_dict(data.get("vsMode")),
        )

    @property
    def is_online(self) -> bool:
        return self.online_state not in (None, "OFFLINE")

    @property
    def is_playing(self) -> bool:
        return self.online_state in ("VS_MODE_MATCHING", "COOP_MODE_MATCHING")


@dataclass
class FriendList:
    """好友列表"""
    friends: List[Friend] = field(default_factory=list)
    total_count: int = 0

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["FriendList"]:
        if not data or "data" not in data:
            return None
        data_inner = data.get("data") or {}
        friends_data = data_inner.get("friends") or {}
        friends = [
            Friend.from_dict(f)
            for f in friends_data.get("nodes") or []
            if f
        ]
        return cls(
            friends=[f for f in friends if f],
            total_count=friends_data.get("totalCount", len(friends)),
        )

    @property
    def online_friends(self) -> List[Friend]:
        return [f for f in self.friends if f.is_online]


# ============================================================
# 玩家模型
# ============================================================

@dataclass
class Badge:
    """徽章"""
    id: str
    image: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["Badge"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            image=Image.from_dict(data.get("image")),
        )


@dataclass
class NameplateBackground:
    """铭牌背景"""
    id: str
    image: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["NameplateBackground"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            image=Image.from_dict(data.get("image")),
        )


@dataclass
class Nameplate:
    """铭牌"""
    badges: List[Badge] = field(default_factory=list)
    background: Optional[NameplateBackground] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["Nameplate"]:
        if not data:
            return None
        badges = [Badge.from_dict(b) for b in data.get("badges", []) if b]
        return cls(
            badges=[b for b in badges if b],
            background=NameplateBackground.from_dict(data.get("background")),
        )


@dataclass
class CurrentPlayer:
    """当前玩家"""
    name: str
    name_id: str
    byname: Optional[str] = None
    nameplate: Optional[Nameplate] = None
    weapon: Optional[Weapon] = None
    head_gear: Optional[Gear] = None
    clothing_gear: Optional[Gear] = None
    shoes_gear: Optional[Gear] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CurrentPlayer"]:
        if not data:
            return None
        return cls(
            name=data.get("name", ""),
            name_id=data.get("nameId", ""),
            byname=data.get("byname"),
            nameplate=Nameplate.from_dict(data.get("nameplate")),
            weapon=Weapon.from_dict(data.get("weapon")),
            head_gear=Gear.from_dict(data.get("headGear")),
            clothing_gear=Gear.from_dict(data.get("clothingGear")),
            shoes_gear=Gear.from_dict(data.get("shoesGear")),
        )

    @property
    def full_name(self) -> str:
        return f"{self.name}#{self.name_id}"


# ============================================================
# 主页模型
# ============================================================

@dataclass
class Banner:
    """轮播图"""
    message: str
    jump_to: str
    image: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["Banner"]:
        if not data:
            return None
        return cls(
            message=data.get("message", ""),
            jump_to=data.get("jumpTo", ""),
            image=Image.from_dict(data.get("image")),
        )


@dataclass
class HomeData:
    """主页数据"""
    current_player: Optional[CurrentPlayer] = None
    banners: List[Banner] = field(default_factory=list)
    friends: List[Friend] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["HomeData"]:
        if not data or "data" not in data:
            return None
        d = data.get("data") or {}
        banners = [Banner.from_dict(b) for b in d.get("banners") or [] if b]
        friends_data = d.get("friends") or {}
        friends = [
            Friend.from_dict(f)
            for f in friends_data.get("nodes") or []
            if f
        ]
        return cls(
            current_player=CurrentPlayer.from_dict(d.get("currentPlayer")),
            banners=[b for b in banners if b],
            friends=[f for f in friends if f],
        )


# ============================================================
# 地图记录模型
# ============================================================

@dataclass
class StageStats:
    """地图统计数据"""
    last_played_time: Optional[str] = None
    win_rate_ar: Optional[float] = None  # 区域
    win_rate_cl: Optional[float] = None  # 蛤蜊
    win_rate_gl: Optional[float] = None  # 鱼虎
    win_rate_lf: Optional[float] = None  # 塔楼
    win_rate_tw: Optional[float] = None  # 涂地

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["StageStats"]:
        if not data:
            return None
        return cls(
            last_played_time=data.get("lastPlayedTime"),
            win_rate_ar=data.get("winRateAr"),
            win_rate_cl=data.get("winRateCl"),
            win_rate_gl=data.get("winRateGl"),
            win_rate_lf=data.get("winRateLf"),
            win_rate_tw=data.get("winRateTw"),
        )


@dataclass
class StageRecord:
    """地图记录"""
    id: str = ""
    name: str = ""
    stage_id: int = 0
    stats: Optional[StageStats] = None
    image: Optional[Image] = None
    original_image: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["StageRecord"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            stage_id=data.get("stageId", 0),
            stats=StageStats.from_dict(data.get("stats")),
            image=Image.from_dict(data.get("image")),
            original_image=Image.from_dict(data.get("originalImage")),
        )


@dataclass
class StageRecords:
    """地图记录列表"""
    stages: List[StageRecord] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["StageRecords"]:
        if not data or "data" not in data:
            return None
        d = data.get("data") or {}
        stage_records = d.get("stageRecords") or {}
        stages = [
            StageRecord.from_dict(s)
            for s in stage_records.get("nodes") or []
            if s
        ]
        return cls(stages=[s for s in stages if s])


# ============================================================
# 武器记录模型
# ============================================================

@dataclass
class WeaponStats:
    """武器统计数据"""
    last_used_time: Optional[str] = None
    level: int = 0
    exp_to_level_up: int = 0
    win: int = 0
    vibes: float = 0.0
    paint: int = 0
    max_weapon_power: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["WeaponStats"]:
        if not data:
            return None
        return cls(
            last_used_time=data.get("lastUsedTime"),
            level=data.get("level", 0),
            exp_to_level_up=data.get("expToLevelUp", 0),
            win=data.get("win", 0),
            vibes=data.get("vibes", 0.0),
            paint=data.get("paint", 0),
            max_weapon_power=data.get("maxWeaponPower"),
        )


@dataclass
class WeaponRecord:
    """武器记录"""
    id: str = ""
    name: str = ""
    weapon_id: int = 0
    stats: Optional[WeaponStats] = None
    sub_weapon: Optional[SubWeapon] = None
    special_weapon: Optional[SpecialWeapon] = None
    image_2d: Optional[Image] = None
    image_3d: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["WeaponRecord"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            weapon_id=data.get("weaponId", 0),
            stats=WeaponStats.from_dict(data.get("stats")),
            sub_weapon=SubWeapon.from_dict(data.get("subWeapon")),
            special_weapon=SpecialWeapon.from_dict(data.get("specialWeapon")),
            image_2d=Image.from_dict(data.get("image2d")),
            image_3d=Image.from_dict(data.get("image3d")),
        )


@dataclass
class WeaponRecords:
    """武器记录列表"""
    weapons: List[WeaponRecord] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["WeaponRecords"]:
        if not data or "data" not in data:
            return None
        d = data.get("data") or {}
        weapon_records = d.get("weaponRecords") or {}
        weapons = [
            WeaponRecord.from_dict(w)
            for w in weapon_records.get("nodes") or []
            if w
        ]
        return cls(weapons=[w for w in weapons if w])


# ============================================================
# NS API 模型 (非GraphQL)
# ============================================================

@dataclass
class NSGame:
    """NS游戏信息"""
    name: str = ""
    image_uri: str = ""
    shop_uri: str = ""
    total_play_time: int = 0
    first_played_at: int = 0

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["NSGame"]:
        if not data:
            return None
        return cls(
            name=data.get("name", ""),
            image_uri=data.get("imageUri", ""),
            shop_uri=data.get("shopUri", ""),
            total_play_time=data.get("totalPlayTime", 0),
            first_played_at=data.get("firstPlayedAt", 0),
        )


@dataclass
class NSPresence:
    """NS在线状态"""
    state: str = ""
    updated_at: int = 0
    logout_at: int = 0
    game: Optional[NSGame] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["NSPresence"]:
        if not data:
            return None
        return cls(
            state=data.get("state", ""),
            updated_at=data.get("updatedAt", 0),
            logout_at=data.get("logoutAt", 0),
            game=NSGame.from_dict(data.get("game")) if data.get("game") else None,
        )

    @property
    def is_online(self) -> bool:
        return self.state == "ONLINE"


@dataclass
class NSFriend:
    """NS好友"""
    id: int = 0
    nsa_id: str = ""
    name: str = ""
    image_uri: str = ""
    is_friend: bool = True
    is_favorite_friend: bool = False
    is_service_user: bool = False
    friend_created_at: int = 0
    presence: Optional[NSPresence] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["NSFriend"]:
        if not data:
            return None
        return cls(
            id=data.get("id", 0),
            nsa_id=data.get("nsaId", ""),
            name=data.get("name", ""),
            image_uri=data.get("imageUri", ""),
            is_friend=data.get("isFriend", True),
            is_favorite_friend=data.get("isFavoriteFriend", False),
            is_service_user=data.get("isServiceUser", False),
            friend_created_at=data.get("friendCreatedAt", 0),
            presence=NSPresence.from_dict(data.get("presence")),
        )

    @property
    def is_online(self) -> bool:
        return self.presence.is_online if self.presence else False


@dataclass
class NSFriendList:
    """NS好友列表"""
    friends: List[NSFriend] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["NSFriendList"]:
        if not data:
            return None
        # NS API 返回的是 JSON 字符串，需要先解析
        if isinstance(data, str):
            import json
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return None
        result = data.get("result") or {}
        friends = [
            NSFriend.from_dict(f)
            for f in result.get("friends") or []
            if f
        ]
        return cls(friends=[f for f in friends if f])

    @property
    def online_friends(self) -> List[NSFriend]:
        return [f for f in self.friends if f.is_online]


@dataclass
class NSMyself:
    """NS个人信息"""
    id: int = 0
    nsa_id: str = ""
    name: str = ""
    image_uri: str = ""
    support_id: str = ""
    friend_code: str = ""
    presence: Optional[NSPresence] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["NSMyself"]:
        if not data:
            return None
        # NS API 返回的是 JSON 字符串
        if isinstance(data, str):
            import json
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return None
        result = data.get("result") or {}
        links = result.get("links") or {}
        friend_code_data = links.get("friendCode") or {}
        return cls(
            id=result.get("id", 0),
            nsa_id=result.get("nsaId", ""),
            name=result.get("name", ""),
            image_uri=result.get("imageUri", ""),
            support_id=result.get("supportId", ""),
            friend_code=friend_code_data.get("id", ""),
            presence=NSPresence.from_dict(result.get("presence")),
        )


# ============================================================
# 历史总结模型
# ============================================================

@dataclass
class XMatchMax:
    """X赛最高分"""
    power: Optional[float] = None
    rank: Optional[int] = None
    power_update_time: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["XMatchMax"]:
        if not data:
            return None
        return cls(
            power=data.get("power"),
            rank=data.get("rank"),
            power_update_time=data.get("powerUpdateTime"),
        )


@dataclass
class MatchPlayHistory:
    """比赛游玩历史"""
    attend: int = 0
    bronze: int = 0
    silver: int = 0
    gold: int = 0

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["MatchPlayHistory"]:
        if not data:
            return None
        return cls(
            attend=data.get("attend", 0),
            bronze=data.get("bronze", 0),
            silver=data.get("silver", 0),
            gold=data.get("gold", 0),
        )


@dataclass
class PlayHistory:
    """游戏历史"""
    current_time: Optional[str] = None
    game_start_time: Optional[str] = None
    rank: int = 0
    udemae: str = ""
    udemae_max: str = ""
    x_match_max_ar: Optional[XMatchMax] = None
    x_match_max_cl: Optional[XMatchMax] = None
    x_match_max_gl: Optional[XMatchMax] = None
    x_match_max_lf: Optional[XMatchMax] = None
    win_count_total: int = 0
    paint_point_total: int = 0
    bankara_match_open_play_history: Optional[MatchPlayHistory] = None
    league_match_play_history: Optional[MatchPlayHistory] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["PlayHistory"]:
        if not data:
            return None
        return cls(
            current_time=data.get("currentTime"),
            game_start_time=data.get("gameStartTime"),
            rank=data.get("rank", 0),
            udemae=data.get("udemae", ""),
            udemae_max=data.get("udemaeMax", ""),
            x_match_max_ar=XMatchMax.from_dict(data.get("xMatchMaxAr")),
            x_match_max_cl=XMatchMax.from_dict(data.get("xMatchMaxCl")),
            x_match_max_gl=XMatchMax.from_dict(data.get("xMatchMaxGl")),
            x_match_max_lf=XMatchMax.from_dict(data.get("xMatchMaxLf")),
            win_count_total=data.get("winCountTotal", 0),
            paint_point_total=data.get("paintPointTotal", 0),
            bankara_match_open_play_history=MatchPlayHistory.from_dict(data.get("bankaraMatchOpenPlayHistory")),
            league_match_play_history=MatchPlayHistory.from_dict(data.get("leagueMatchPlayHistory")),
        )


@dataclass
class HistorySummary:
    """历史总结"""
    current_player: Optional[CurrentPlayer] = None
    play_history: Optional[PlayHistory] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["HistorySummary"]:
        if not data or "data" not in data:
            return None
        d = data.get("data") or {}
        return cls(
            current_player=CurrentPlayer.from_dict(d.get("currentPlayer")),
            play_history=PlayHistory.from_dict(d.get("playHistory")),
        )


# ============================================================
# 对战玩家详情模型
# ============================================================

@dataclass
class VsPlayerDetail:
    """对战玩家详情（含装备）"""
    id: str
    name: str
    name_id: str
    byname: Optional[str] = None
    species: Optional[str] = None  # INKLING, OCTOLING
    nameplate: Optional[Nameplate] = None
    weapon: Optional[Weapon] = None
    head_gear: Optional[GearDetail] = None
    clothing_gear: Optional[GearDetail] = None
    shoes_gear: Optional[GearDetail] = None
    paint: int = 0
    is_myself: bool = False

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["VsPlayerDetail"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            name_id=data.get("nameId", ""),
            byname=data.get("byname"),
            species=data.get("species"),
            nameplate=Nameplate.from_dict(data.get("nameplate")),
            weapon=Weapon.from_dict(data.get("weapon")),
            head_gear=GearDetail.from_dict(data.get("headGear")),
            clothing_gear=GearDetail.from_dict(data.get("clothingGear")),
            shoes_gear=GearDetail.from_dict(data.get("shoesGear")),
            paint=data.get("paint", 0),
            is_myself=data.get("isMyself", False),
        )

    @property
    def decoded_id(self) -> DecodedId:
        return DecodedId.decode(self.id)

    @property
    def full_name(self) -> str:
        return f"{self.name}#{self.name_id}"


# ============================================================
# 打工玩家详情模型
# ============================================================

@dataclass
class CoopUniform:
    """打工制服"""
    id: str
    name: str
    image: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopUniform"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            image=Image.from_dict(data.get("image")),
        )


@dataclass
class CoopWeapon:
    """打工武器（简化版）"""
    name: str
    image: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopWeapon"]:
        if not data:
            return None
        return cls(
            name=data.get("name", ""),
            image=Image.from_dict(data.get("image")),
        )


@dataclass
class CoopSpecialWeapon:
    """打工特殊武器"""
    weapon_id: int = 0
    name: str = ""
    image: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopSpecialWeapon"]:
        if not data:
            return None
        return cls(
            weapon_id=data.get("weaponId", 0),
            name=data.get("name", ""),
            image=Image.from_dict(data.get("image")),
        )


@dataclass
class CoopPlayerDetail:
    """打工玩家详情"""
    id: str
    name: str
    name_id: str
    byname: Optional[str] = None
    species: Optional[str] = None
    nameplate: Optional[Nameplate] = None
    uniform: Optional[CoopUniform] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopPlayerDetail"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            name_id=data.get("nameId", ""),
            byname=data.get("byname"),
            species=data.get("species"),
            nameplate=Nameplate.from_dict(data.get("nameplate")),
            uniform=CoopUniform.from_dict(data.get("uniform")),
        )

    @property
    def decoded_id(self) -> DecodedId:
        return DecodedId.decode(self.id)


@dataclass
class CoopPlayerResult:
    """打工玩家战绩"""
    player: Optional[CoopPlayerDetail] = None
    weapons: List[CoopWeapon] = field(default_factory=list)
    special_weapon: Optional[CoopSpecialWeapon] = None
    defeat_enemy_count: int = 0
    deliver_count: int = 0
    golden_assist_count: int = 0
    golden_deliver_count: int = 0
    rescue_count: int = 0
    rescued_count: int = 0

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopPlayerResult"]:
        if not data:
            return None
        weapons = [
            CoopWeapon.from_dict(w)
            for w in data.get("weapons") or []
            if w
        ]
        return cls(
            player=CoopPlayerDetail.from_dict(data.get("player")),
            weapons=[w for w in weapons if w],
            special_weapon=CoopSpecialWeapon.from_dict(data.get("specialWeapon")),
            defeat_enemy_count=data.get("defeatEnemyCount", 0),
            deliver_count=data.get("deliverCount", 0),
            golden_assist_count=data.get("goldenAssistCount", 0),
            golden_deliver_count=data.get("goldenDeliverCount", 0),
            rescue_count=data.get("rescueCount", 0),
            rescued_count=data.get("rescuedCount", 0),
        )


# ============================================================
# 对战队伍模型
# ============================================================

@dataclass
class TeamColor:
    """队伍颜色"""
    a: float = 1.0
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["TeamColor"]:
        if not data:
            return None
        return cls(
            a=data.get("a", 1.0),
            r=data.get("r", 0.0),
            g=data.get("g", 0.0),
            b=data.get("b", 0.0),
        )


@dataclass
class VsTeamResult:
    """对战队伍结果"""
    paint_ratio: Optional[float] = None
    score: Optional[int] = None
    noroshi: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["VsTeamResult"]:
        if not data:
            return None
        return cls(
            paint_ratio=data.get("paintRatio"),
            score=data.get("score"),
            noroshi=data.get("noroshi"),
        )


@dataclass
class VsTeam:
    """对战队伍"""
    color: Optional[TeamColor] = None
    result: Optional[VsTeamResult] = None
    judgement: Optional[str] = None
    players: List[VsPlayerDetail] = field(default_factory=list)
    tricolor_role: Optional[str] = None
    fest_team_name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["VsTeam"]:
        if not data:
            return None
        players = [
            VsPlayerDetail.from_dict(p)
            for p in data.get("players") or []
            if p
        ]
        return cls(
            color=TeamColor.from_dict(data.get("color")),
            result=VsTeamResult.from_dict(data.get("result")),
            judgement=data.get("judgement"),
            players=[p for p in players if p],
            tricolor_role=data.get("tricolorRole"),
            fest_team_name=data.get("festTeamName"),
        )


# ============================================================
# 完整对战详情模型
# ============================================================

@dataclass
class VsHistoryDetailFull:
    """完整对战详情"""
    id: str
    vs_mode: Optional[VsMode] = None
    vs_rule: Optional[VsRule] = None
    vs_stage: Optional[VsStage] = None
    judgement: Optional[str] = None
    knockout: Optional[str] = None
    player: Optional[VsPlayerDetail] = None
    my_team: Optional[VsTeam] = None
    other_teams: List[VsTeam] = field(default_factory=list)
    udemae: Optional[str] = None
    bankara_match: Optional[BankaraMatch] = None
    played_time: Optional[str] = None
    duration: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["VsHistoryDetailFull"]:
        if not data or "data" not in data:
            return None
        d = data.get("data") or {}
        detail = d.get("vsHistoryDetail") or {}
        other_teams = [
            VsTeam.from_dict(t)
            for t in detail.get("otherTeams") or []
            if t
        ]
        return cls(
            id=detail.get("id", ""),
            vs_mode=VsMode.from_dict(detail.get("vsMode")),
            vs_rule=VsRule.from_dict(detail.get("vsRule")),
            vs_stage=VsStage.from_dict(detail.get("vsStage")),
            judgement=detail.get("judgement"),
            knockout=detail.get("knockout"),
            player=VsPlayerDetail.from_dict(detail.get("player")),
            my_team=VsTeam.from_dict(detail.get("myTeam")),
            other_teams=[t for t in other_teams if t],
            udemae=detail.get("udemae"),
            bankara_match=BankaraMatch.from_dict(detail.get("bankaraMatch")),
            played_time=detail.get("playedTime"),
            duration=detail.get("duration"),
        )

    @property
    def decoded_id(self) -> DecodedId:
        return DecodedId.decode(self.id)

    @property
    def is_win(self) -> bool:
        return self.judgement == "WIN"


# ============================================================
# 完整打工详情模型
# ============================================================

@dataclass
class CoopEnemy:
    """打工敌人"""
    id: str
    name: str
    image: Optional[Image] = None

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopEnemy"]:
        if not data:
            return None
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            image=Image.from_dict(data.get("image")),
        )


@dataclass
class CoopEnemyResult:
    """打工敌人战绩"""
    enemy: Optional[CoopEnemy] = None
    defeat_count: int = 0
    team_defeat_count: int = 0
    pop_count: int = 0

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopEnemyResult"]:
        if not data:
            return None
        return cls(
            enemy=CoopEnemy.from_dict(data.get("enemy")),
            defeat_count=data.get("defeatCount", 0),
            team_defeat_count=data.get("teamDefeatCount", 0),
            pop_count=data.get("popCount", 0),
        )


@dataclass
class CoopBossResult:
    """打工头目战绩"""
    boss: Optional[CoopEnemy] = None
    has_defeat_boss: bool = False

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopBossResult"]:
        if not data:
            return None
        return cls(
            boss=CoopEnemy.from_dict(data.get("boss")),
            has_defeat_boss=data.get("hasDefeatBoss", False),
        )


@dataclass
class CoopWave:
    """打工波次"""
    wave_number: int = 0
    water_level: int = 0
    event_wave: Optional[str] = None
    deliver_norm: Optional[int] = None
    golden_pop_count: int = 0
    team_deliver_count: Optional[int] = None
    special_weapons: List[CoopSpecialWeapon] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopWave"]:
        if not data:
            return None
        specials = [
            CoopSpecialWeapon.from_dict(s)
            for s in data.get("specialWeapons") or []
            if s
        ]
        event = data.get("eventWave") or {}
        return cls(
            wave_number=data.get("waveNumber", 0),
            water_level=data.get("waterLevel", 0),
            event_wave=event.get("name") if event else None,
            deliver_norm=data.get("deliverNorm"),
            golden_pop_count=data.get("goldenPopCount", 0),
            team_deliver_count=data.get("teamDeliverCount"),
            special_weapons=[s for s in specials if s],
        )


@dataclass
class CoopHistoryDetailFull:
    """完整打工详情"""
    id: str
    coop_stage: Optional[CoopStage] = None
    after_grade: Optional[CoopGrade] = None
    after_grade_point: Optional[int] = None
    grade_point_diff: Optional[str] = None
    danger_rate: Optional[float] = None
    result_wave: int = 0
    played_time: Optional[str] = None
    my_result: Optional[CoopPlayerResult] = None
    member_results: List[CoopPlayerResult] = field(default_factory=list)
    boss_result: Optional[CoopBossResult] = None
    boss_results: List[CoopBossResult] = field(default_factory=list)
    enemy_results: List[CoopEnemyResult] = field(default_factory=list)
    wave_results: List[CoopWave] = field(default_factory=list)
    weapons: List[CoopWeapon] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["CoopHistoryDetailFull"]:
        if not data or "data" not in data:
            return None
        d = data.get("data") or {}
        detail = d.get("coopHistoryDetail") or {}
        member_results = [
            CoopPlayerResult.from_dict(m)
            for m in detail.get("memberResults") or []
            if m
        ]
        boss_results = [
            CoopBossResult.from_dict(b)
            for b in detail.get("bossResults") or []
            if b
        ]
        enemy_results = [
            CoopEnemyResult.from_dict(e)
            for e in detail.get("enemyResults") or []
            if e
        ]
        wave_results = [
            CoopWave.from_dict(w)
            for w in detail.get("waveResults") or []
            if w
        ]
        weapons = [
            CoopWeapon.from_dict(w)
            for w in detail.get("weapons") or []
            if w
        ]
        return cls(
            id=detail.get("id", ""),
            coop_stage=CoopStage.from_dict(detail.get("coopStage")),
            after_grade=CoopGrade.from_dict(detail.get("afterGrade")),
            after_grade_point=detail.get("afterGradePoint"),
            grade_point_diff=detail.get("gradePointDiff"),
            danger_rate=detail.get("dangerRate"),
            result_wave=detail.get("resultWave", 0),
            played_time=detail.get("playedTime"),
            my_result=CoopPlayerResult.from_dict(detail.get("myResult")),
            member_results=[m for m in member_results if m],
            boss_result=CoopBossResult.from_dict(detail.get("bossResult")),
            boss_results=[b for b in boss_results if b],
            enemy_results=[e for e in enemy_results if e],
            wave_results=[w for w in wave_results if w],
            weapons=[w for w in weapons if w],
        )

    @property
    def decoded_id(self) -> DecodedId:
        return DecodedId.decode(self.id)

    @property
    def is_clear(self) -> bool:
        return self.result_wave == 0

    @property
    def all_players(self) -> List[CoopPlayerResult]:
        """所有玩家（包括自己）"""
        results = []
        if self.my_result:
            results.append(self.my_result)
        results.extend(self.member_results)
        return results
