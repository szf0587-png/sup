"""认证 API 路由 - 用户注册、登录、登出"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import uuid

from server.database import get_db
from server.models.user import User
from server.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserInfoResponse,
    MessageResponse,
    UserUpdateRequest,
    PasswordChangeRequest
)
from server.utils.password import hash_password, verify_password
from server.utils.jwt_utils import create_access_token, ACCESS_TOKEN_EXPIRE_HOURS
from server.middleware.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=UserInfoResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册

    - 检查用户名和邮箱是否已存在
    - 密码使用 bcrypt 加密存储
    - 自动生成 user_xxx 格式的 UUID
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被使用"
        )

    # 创建新用户
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    new_user = User(
        id=user_id,
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        display_name=request.display_name or request.username,
        role="user",
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenResponse)
def login(
    request: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    用户登录

    - 支持用户名或邮箱登录
    - 验证密码
    - 返回 JWT 令牌，同时设置 HTTPOnly Cookie
    - 更新最后登录时间
    """
    # 查找用户（用户名或邮箱）
    user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 检查账号是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )

    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    db.commit()

    # 生成 JWT 令牌
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username}
    )

    # 设置 HTTPOnly Cookie（更安全，防止 XSS 攻击）
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,  # 8小时
        samesite="lax",  # CSRF 保护
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600
    )


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response):
    """
    用户登出

    - 清除 HTTPOnly Cookie
    - 客户端应同时清除本地存储的令牌
    """
    response.delete_cookie(key="access_token")
    return MessageResponse(message="登出成功")


@router.get("/me", response_model=UserInfoResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户信息

    需要认证：是
    """
    return current_user


@router.put("/me", response_model=UserInfoResponse)
def update_current_user(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新当前用户信息

    - 可更新显示名称和邮箱
    - 需要认证：是
    """
    if request.display_name is not None:
        current_user.display_name = request.display_name

    if request.email is not None:
        # 检查新邮箱是否已被其他用户使用
        existing_email = db.query(User).filter(
            User.email == request.email,
            User.id != current_user.id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
        current_user.email = request.email

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改当前用户密码

    - 需要验证旧密码
    - 需要认证：是
    """
    # 验证旧密码
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    # 更新密码
    current_user.password_hash = hash_password(request.new_password)
    db.commit()

    return MessageResponse(message="密码修改成功", detail="请使用新密码重新登录")
