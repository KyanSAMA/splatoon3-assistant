"""系统配置模型"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.dao.database import Base


class ConfigEntry(Base):
    """系统配置键值对"""
    __tablename__ = "config"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, default="str")
    description: Mapped[str] = mapped_column(String, nullable=True)
