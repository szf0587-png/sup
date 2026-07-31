"""JWT 令牌工具 - 用于生成和验证用户身份令牌"""
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8  # 令牌有效期 8 小时


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌

    Args:
        data: 要编码到令牌中的数据（通常包含 user_id, username 等）
        expires_delta: 自定义过期时间（可选）

    Returns:
        JWT 令牌字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Optional[dict]:
    """
    验证 JWT 令牌并解码

    Args:
        token: JWT 令牌字符串

    Returns:
        解码后的数据字典，如果令牌无效或过期则返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # 令牌已过期
        return None
    except jwt.InvalidTokenError:
        # 令牌无效
        return None


def decode_token_without_verification(token: str) -> Optional[dict]:
    """
    不验证签名直接解码令牌（仅用于调试）

    Args:
        token: JWT 令牌字符串

    Returns:
        解码后的数据字典
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception:
        return None
