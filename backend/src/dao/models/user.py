"""用户相关 ORM 模型"""

from typing import Optional
from sqlalchemy import String, Integer, Float, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class User(Base):
    """用户表"""
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nsa_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    splatoon_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    session_token: Mapped[str] = mapped_column(String, nullable=False)
    access_token: Mapped[str] = mapped_column(String, nullable=False)
    g_token: Mapped[str] = mapped_column(String, nullable=False)
    bullet_token: Mapped[str] = mapped_column(String, nullable=False)
    user_lang: Mapped[str] = mapped_column(String, nullable=False, default="zh-CN")
    user_country: Mapped[str] = mapped_column(String, nullable=False, default="JP")
    user_nickname: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_current: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_login_at: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nsa_id": self.nsa_id,
            "splatoon_id": self.splatoon_id,
            "session_token": self.session_token,
            "access_token": self.access_token,
            "g_token": self.g_token,
            "bullet_token": self.bullet_token,
            "user_lang": self.user_lang,
            "user_country": self.user_country,
            "user_nickname": self.user_nickname,
            "is_current": self.is_current,
            "last_login_at": self.last_login_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class UserStageRecord(Base):
    """用户地图胜率表"""
    __tablename__ = "user_stage_record"
    __table_args__ = (UniqueConstraint("user_id", "vs_stage_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    stage_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vs_stage_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    stage_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    last_played_time: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    win_rate_ar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    win_rate_cl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    win_rate_gl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    win_rate_lf: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    win_rate_tw: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class UserWeaponRecord(Base):
    """用户武器战绩表"""
    __tablename__ = "user_weapon_record"
    __table_args__ = (UniqueConstraint("user_id", "main_weapon_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    main_weapon_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    main_weapon_name: Mapped[str] = mapped_column(String, nullable=False)
    last_used_time: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exp_to_level_up: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    win: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vibes: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    paint: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_weapon_power: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_weapon_power: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
