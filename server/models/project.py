"""项目模型"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey, Text
from server.database import Base


class Project(Base):
    """项目表 - 用户的研究项目/工作空间"""
    __tablename__ = "projects"

    id = Column(String, primary_key=True)  # UUID: project_xxx
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String, nullable=False, comment="项目名称")
    description = Column(Text, nullable=True, comment="项目描述")

    # 项目配置
    region = Column(JSON, nullable=True, comment="研究区域边界 {type: Polygon, coordinates: [[[...]]]}")
    config = Column(JSON, nullable=True, comment="项目配置（默认参数、可视化设置等）")

    # 关联的数据集ID列表
    dataset_ids = Column(JSON, nullable=True, comment="关联的数据集ID列表 [dataset_xxx, ...]")

    # 激活状态（用户同时只能有一个激活项目）
    is_active = Column(Boolean, default=False, nullable=False, comment="是否为当前激活项目")
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, user_id={self.user_id}, active={self.is_active})>"
