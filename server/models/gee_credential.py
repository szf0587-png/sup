"""GEE凭证模型"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from server.database import Base


class GEECredential(Base):
    """GEE凭证表 - 存储用户绑定的Google Earth Engine账号信息"""
    __tablename__ = "gee_credentials"

    id = Column(String, primary_key=True)  # UUID: gee_xxx
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # GEE认证信息
    gee_email = Column(String, nullable=False, comment="GEE账号邮箱")
    gee_project_id = Column(String, nullable=False, comment="GEE项目ID")

    # OAuth凭证（加密存储）
    service_account_json = Column(Text, nullable=True, comment="服务账号JSON密钥（加密）")
    refresh_token = Column(Text, nullable=True, comment="OAuth刷新令牌（加密）")

    # 状态
    is_verified = Column(Boolean, default=False, nullable=False, comment="凭证是否已验证")
    last_verified_at = Column(DateTime, nullable=True, comment="最后验证时间")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<GEECredential(id={self.id}, user_id={self.user_id}, email={self.gee_email}, verified={self.is_verified})>"
