"""打工相关 ORM 模型"""

from typing import Optional
from sqlalchemy import String, Integer, Float, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class CoopDetail(Base):
    """打工详情主表"""
    __tablename__ = "coop_detail"
    __table_args__ = (UniqueConstraint("user_id", "splatoon_id", "played_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    splatoon_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    played_time: Mapped[str] = mapped_column(String, nullable=False)
    rule: Mapped[str] = mapped_column(String, nullable=False, index=True)
    danger_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    result_wave: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    smell_meter: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stage_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    stage_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    after_grade_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    after_grade_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    after_grade_point: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    boss_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    boss_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    boss_defeated: Mapped[int] = mapped_column(Integer, default=0)
    scale_gold: Mapped[int] = mapped_column(Integer, default=0)
    scale_silver: Mapped[int] = mapped_column(Integer, default=0)
    scale_bronze: Mapped[int] = mapped_column(Integer, default=0)
    job_point: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    job_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    job_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    job_bonus: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updated_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class CoopPlayer(Base):
    """打工玩家表"""
    __tablename__ = "coop_player"
    __table_args__ = (UniqueConstraint("coop_id", "player_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    coop_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    player_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_myself: Mapped[int] = mapped_column(Integer, default=0)
    player_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    name_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    byname: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    species: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    uniform_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    uniform_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    special_weapon_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    special_weapon_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    weapons: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    weapon_names: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    defeat_enemy_count: Mapped[int] = mapped_column(Integer, default=0)
    deliver_count: Mapped[int] = mapped_column(Integer, default=0)
    golden_assist_count: Mapped[int] = mapped_column(Integer, default=0)
    golden_deliver_count: Mapped[int] = mapped_column(Integer, default=0)
    rescue_count: Mapped[int] = mapped_column(Integer, default=0)
    rescued_count: Mapped[int] = mapped_column(Integer, default=0)
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class CoopWave(Base):
    """打工波次表"""
    __tablename__ = "coop_wave"
    __table_args__ = (UniqueConstraint("coop_id", "wave_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    coop_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    wave_number: Mapped[int] = mapped_column(Integer, nullable=False)
    water_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    event_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    event_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    deliver_norm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    golden_pop_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    team_deliver_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    special_weapons: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    special_weapon_names: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class CoopEnemy(Base):
    """打工敌人统计表"""
    __tablename__ = "coop_enemy"
    __table_args__ = (UniqueConstraint("coop_id", "enemy_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    coop_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    enemy_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    enemy_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    defeat_count: Mapped[int] = mapped_column(Integer, default=0)
    team_defeat_count: Mapped[int] = mapped_column(Integer, default=0)
    pop_count: Mapped[int] = mapped_column(Integer, default=0)
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class CoopBoss(Base):
    """打工Boss结果表"""
    __tablename__ = "coop_boss"
    __table_args__ = (UniqueConstraint("coop_id", "boss_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    coop_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    boss_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    boss_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    has_defeat_boss: Mapped[int] = mapped_column(Integer, default=0)
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
