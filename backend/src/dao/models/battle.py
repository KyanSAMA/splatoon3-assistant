"""对战相关 ORM 模型"""

from typing import Optional
from sqlalchemy import String, Integer, Float, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class BattleDetail(Base):
    """对战详情主表

    字段说明:
    - vs_stage_id: 关联 Stage.vs_stage_id，获取地图图片需查询 Stage 表获取 code
      图片路径: /static/stage/{stage.code}.png
    - vs_mode: BANKARA/REGULAR/X_MATCH/LEAGUE/FEST/PRIVATE
    - vs_rule: AREA/LOFT/GOAL/CLAM/TURF_WAR
    - judgement: WIN/LOSE/EXEMPTED_LOSE/DEEMED_LOSE/DRAW
    - knockout: WIN/LOSE/NEITHER (KO状态)
    - bankara_mode: OPEN/CHALLENGE (仅BANKARA模式有效)
    """
    __tablename__ = "battle_detail"
    __table_args__ = (UniqueConstraint("user_id", "splatoon_id", "played_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    splatoon_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    base64_decode_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    played_time: Mapped[str] = mapped_column(String, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    vs_mode: Mapped[str] = mapped_column(String, nullable=False)
    vs_rule: Mapped[str] = mapped_column(String, nullable=False)
    vs_stage_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    judgement: Mapped[str] = mapped_column(String, nullable=False, index=True)
    knockout: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bankara_mode: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    udemae: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    x_power: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fest_power: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weapon_power: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    my_league_power: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    league_match_event_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mode_extra: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    awards: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updated_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class BattleTeam(Base):
    """队伍表"""
    __tablename__ = "battle_team"
    __table_args__ = (UniqueConstraint("battle_id", "team_role", "team_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    battle_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_role: Mapped[str] = mapped_column(String, nullable=False)
    team_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    paint_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    noroshi: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    judgement: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    fest_team_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    fest_uniform_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    fest_uniform_bonus_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fest_streak_win_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tricolor_role: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class BattlePlayer(Base):
    """玩家表

    字段说明:
    - weapon_id: 直接对应 MainWeapon.code，图片路径: /static/weapon/{weapon_id}.png
    - is_myself: 1=自己, 0=其他玩家
    - species: INKLING/OCTOLING
    - crown: X赛王冠 (1=有)
    """
    __tablename__ = "battle_player"
    __table_args__ = (UniqueConstraint("battle_id", "team_id", "player_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    battle_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    player_order: Mapped[int] = mapped_column(Integer, nullable=False)
    player_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    name_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    byname: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    species: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_myself: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weapon_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    head_main_skill: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    head_additional_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    clothing_main_skill: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    clothing_additional_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    shoes_main_skill: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    shoes_additional_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    head_skills_images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    clothing_skills_images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    shoes_skills_images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    paint: Mapped[int] = mapped_column(Integer, default=0)
    kill_count: Mapped[int] = mapped_column(Integer, default=0)
    assist_count: Mapped[int] = mapped_column(Integer, default=0)
    death_count: Mapped[int] = mapped_column(Integer, default=0)
    special_count: Mapped[int] = mapped_column(Integer, default=0)
    noroshi_try: Mapped[int] = mapped_column(Integer, default=0)
    crown: Mapped[int] = mapped_column(Integer, default=0)
    fest_dragon_cert: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class BattleAward(Base):
    """徽章表"""
    __tablename__ = "battle_award"
    __table_args__ = (UniqueConstraint("battle_id", "award_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    battle_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    award_name: Mapped[str] = mapped_column(String, nullable=False)
    award_rank: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
