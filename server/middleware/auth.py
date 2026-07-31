"""认证中间件 - 提供用户身份验证和依赖注入"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie, Header
from sqlalchemy.orm import Session

from server.database import get_db
from server.models.user import User
from server.utils.jwt_utils import verify_access_token


def get_token_from_request(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
) -> Optional[str]:
    """
    从请求中提取 JWT 令牌（支持两种方式）

    1. Authorization Header: "Bearer <token>"
    2. Cookie: access_token=<token>

    Args:
        authorization: Authorization 请求头
        access_token: Cookie 中的令牌

    Returns:
        JWT 令牌字符串，如果都不存在则返回 None
    """
    # 优先从 Authorization Header 获取
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")

    # 其次从 Cookie 获取
    if access_token:
        return access_token

    return None


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户（必须登录）

    用法：
        @app.get("/api/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}

    Args:
        token: JWT 令牌
        db: 数据库会话

    Returns:
        当前用户对象

    Raises:
        HTTPException: 401 未授权（令牌无效/过期/用户不存在）
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证身份凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    # 验证令牌
    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception

    # 提取用户 ID
    user_id: str = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账号已被禁用"
        )

    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    获取当前登录用户（可选，不登录也能访问）

    用法：
        @app.get("/api/public")
        def public_route(current_user: Optional[User] = Depends(get_current_user_optional)):
            if current_user:
                return {"message": f"欢迎，{current_user.username}"}
            else:
                return {"message": "欢迎访问"}

    Args:
        token: JWT 令牌
        db: 数据库会话

    Returns:
        当前用户对象，如果未登录则返回 None
    """
    if not token:
        return None

    payload = verify_access_token(token)
    if payload is None:
        return None

    user_id: str = payload.get("user_id")
    if user_id is None:
        return None

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    要求管理员权限

    用法：
        @app.delete("/api/users/{user_id}")
        def delete_user(user_id: str, admin: User = Depends(require_admin)):
            # 只有管理员能访问
            pass

    Args:
        current_user: 当前用户

    Returns:
        当前用户（必须是管理员）

    Raises:
        HTTPException: 403 权限不足
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user
