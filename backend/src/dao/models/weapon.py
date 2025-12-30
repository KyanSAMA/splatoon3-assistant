"""武器相关 ORM 模型"""

from typing import Optional
from sqlalchemy import String, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SubWeapon(Base):
    """副武器表"""
    __tablename__ = "sub_weapon"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    ink_consume: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    zh_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class SpecialWeapon(Base):
    """特殊武器表"""
    __tablename__ = "special_weapon"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    zh_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class MainWeapon(Base):
    """主武器表"""
    __tablename__ = "main_weapon"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    special_point: Mapped[int] = mapped_column(Integer, nullable=False)
    sub_weapon_code: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    special_weapon_code: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    zh_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    weapon_class: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    distance_class: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Skill(Base):
    """装备能力表"""
    __tablename__ = "skill"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    zh_name: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    zh_desc: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
