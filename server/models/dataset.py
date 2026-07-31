"""数据集模型"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text
from server.database import Base


class Dataset(Base):
    """数据集表 - 存储用户上传的矢量/栅格数据"""
    __tablename__ = "datasets"

    id = Column(String, primary_key=True)  # UUID: dataset_xxx
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String, nullable=False, comment="数据集名称")
    description = Column(Text, nullable=True, comment="数据集描述")
    dataset_type = Column(String, nullable=False, comment="数据类型: vector/raster/gee")

    # 文件存储路径（相对路径：users/{user_id}/vector|raster/{filename}）
    file_path = Column(String, nullable=False, comment="文件相对路径")
    file_size = Column(Integer, nullable=True, comment="文件大小(bytes)")

    # 地理信息
    crs = Column(String, nullable=True, comment="坐标参考系统")
    bounds = Column(JSON, nullable=True, comment="边界范围 [minx, miny, maxx, maxy]")

    # 元数据（注意：metadata 是 SQLAlchemy 保留字段，改用 extra_metadata）
    extra_metadata = Column(JSON, nullable=True, comment="额外元数据（字段信息、波段信息等）")

    # iServer 服务关联
    iserver_service_id = Column(String, ForeignKey("iserver_services.id"), nullable=True, index=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Dataset(id={self.id}, name={self.name}, type={self.dataset_type}, user_id={self.user_id})>"
