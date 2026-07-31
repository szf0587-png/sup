"""认证相关的 Pydantic 模型 - 用于 API 请求和响应的数据验证"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名（3-50字符）")
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=100, description="密码（至少6字符）")
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """验证邮箱格式"""
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, v):
            raise ValueError('邮箱格式不正确')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "zhangsan",
                "email": "zhangsan@example.com",
                "password": "password123",
                "display_name": "张三"
            }
        }


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "admin123"
            }
        }


class TokenResponse(BaseModel):
    """JWT 令牌响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    email: str
    display_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True  # 允许从 ORM 模型创建


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    detail: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "操作成功",
                "detail": "用户已创建"
            }
        }


class UserUpdateRequest(BaseModel):
    """用户信息更新请求"""
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    email: Optional[str] = Field(None, description="邮箱地址")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """验证邮箱格式"""
        if v is None:
            return v
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, v):
            raise ValueError('邮箱格式不正确')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "display_name": "新的显示名称",
                "email": "newemail@example.com"
            }
        }


class PasswordChangeRequest(BaseModel):
    """密码修改请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码（至少6字符）")

    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "oldpass123",
                "new_password": "newpass456"
            }
        }
