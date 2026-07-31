"""金标准数据库模型"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, Text, Boolean
from server.database import Base


class GoldenStandard(Base):
    """金标准表 - 存储用户的作物种植金标准模型"""
    __tablename__ = "golden_standards"

    id = Column(String, primary_key=True)  # UUID: standard_xxx
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)

    # 基本信息
    model_name = Column(String, nullable=False, comment="金标准名称")
    crop_type = Column(String, nullable=False, comment="作物类型")

    # 地理位置
    latitude = Column(Float, nullable=False, comment="纬度")
    longitude = Column(Float, nullable=False, comment="经度")
    location_description = Column(Text, nullable=True, comment="位置描述")

    # 适宜性参数
    suitability_params = Column(JSON, nullable=True, comment="适宜性参数（坡度、海拔、土壤等）")

    # 物候参数
    phenology_params = Column(JSON, nullable=True, comment="物候参数（生长周期、关键物候期等）")

    # 其他元数据
    description = Column(Text, nullable=True, comment="描述")
    source = Column(String, nullable=True, comment="数据来源")
    tags = Column(JSON, nullable=True, comment="标签列表")

    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<GoldenStandard(id={self.id}, name={self.model_name}, crop={self.crop_type}, user_id={self.user_id})>"
