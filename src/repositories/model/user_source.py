
from datetime import datetime
from sqlalchemy import Integer, String, JSON, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from db_wrapper import Base

class UserSource(Base):
    __tablename__ = "user_source"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(32))
    source: Mapped[str | None] = mapped_column(String(20))
    openid: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=False)
    union_id: Mapped[str | None] = mapped_column(String(255))
    extra: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)
