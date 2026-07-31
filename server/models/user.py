"""用户模型"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from server.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # UUID: user_xxx
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    role = Column(String, default="user", nullable=False)  # "admin" / "user"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
