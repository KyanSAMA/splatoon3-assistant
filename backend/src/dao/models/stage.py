"""地图 ORM 模型"""

from typing import Optional
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Stage(Base):
    """地图表"""
    __tablename__ = "stage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vs_stage_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True, nullable=True, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    zh_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    stage_type: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    created_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
