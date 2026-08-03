"""iServer服务模型"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey, Integer
from server.database import Base


class IServerService(Base):
    """iServer服务表 - 追踪已发布的iServer服务"""
    __tablename__ = "iserver_services"

    id = Column(String, primary_key=True)  # UUID: service_xxx
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)

    # 服务命名：{user_prefix}_{dataset_name}，实现命名空间隔离
    service_name = Column(String, unique=True, nullable=False, index=True, comment="iServer服务名称")
    service_type = Column(String, nullable=False, comment="服务类型: data/map/feature/3d")

    # 数据源信息
    datasource_name = Column(String, nullable=False, comment="数据源名称")
    dataset_name = Column(String, nullable=False, comment="数据集名称")

    # 服务URL
    service_url = Column(String, nullable=True, comment="服务访问URL")

    # 服务配置
    service_config = Column(JSON, nullable=True, comment="服务配置参数")

    # 资源使用情况
    request_count = Column(Integer, default=0, nullable=False, comment="请求计数")
    last_accessed_at = Column(DateTime, nullable=True, comment="最后访问时间")

    # 状态
    is_active = Column(Boolean, default=True, nullable=False, comment="服务是否在线")
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<IServerService(id={self.id}, name={self.service_name}, type={self.service_type}, active={self.is_active})>"
