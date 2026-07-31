"""金标准 CRUD API 路由（数据库版本 - 多用户支持）"""
from __future__ import annotations

import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from server.database import get_db
from server.models.user import User
from server.models.golden_standard import GoldenStandard
from server.models.project import Project
from server.middleware.auth import get_current_user, get_current_user_optional
from server.schemas.standards import (
    GoldenStandardCreate,
    GoldenStandard as GoldenStandardSchema,
    GoldenStandardSummary,
    GoldenStandardRename,
    GoldenStandardUpdate,
    GoldenStandardListResponse,
)
from server.schemas.auth import MessageResponse

router = APIRouter(prefix="/api/golden-standards", tags=["golden-standards"])


@router.get("", response_model=GoldenStandardListResponse)
def list_all(
    crop_type: str = None,
    project_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    列出当前用户的所有金标准

    可选筛选：
    - crop_type: 作物类型
    - project_id: 项目ID
    """
    query = db.query(GoldenStandard).filter(
        GoldenStandard.user_id == current_user.id,
        GoldenStandard.is_deleted == False
    )

    if crop_type:
        query = query.filter(GoldenStandard.crop_type == crop_type)

    if project_id:
        query = query.filter(GoldenStandard.project_id == project_id)

    standards = query.order_by(GoldenStandard.created_at.desc()).all()

    return GoldenStandardListResponse(
        total=len(standards),
        standards=[GoldenStandardSchema.model_validate(s) for s in standards]
    )


@router.get("/list", response_model=List[GoldenStandardSummary])
def list_summaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取金标准摘要列表（用于下拉选择）

    只返回必要的字段：id, model_name, crop_type, latitude, longitude
    """
    standards = db.query(GoldenStandard).filter(
        GoldenStandard.user_id == current_user.id,
        GoldenStandard.is_deleted == False
    ).all()

    return [GoldenStandardSummary.model_validate(s) for s in standards]


@router.get("/{standard_id}", response_model=GoldenStandardSchema)
def get_standard(
    standard_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取金标准详情

    只能访问自己的金标准
    """
    standard = db.query(GoldenStandard).filter(
        GoldenStandard.id == standard_id
    ).first()

    if not standard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="金标准不存在"
        )

    # 权限检查
    if standard.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此金标准"
        )

    return standard


@router.post("", response_model=GoldenStandardSchema, status_code=status.HTTP_201_CREATED)
def create(
    standard: GoldenStandardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新的金标准

    如果当前有激活的项目，自动关联到该项目
    """
    # 获取当前激活的项目
    active_project = db.query(Project).filter(
        Project.user_id == current_user.id,
        Project.is_active == True,
        Project.is_deleted == False
    ).first()

    # 生成 ID
    standard_id = f"standard_{uuid.uuid4().hex[:12]}"

    # 兼容旧版 API：如果有 ndvi_curve 和 lst_curve，放到 phenology_params 中
    phenology_params = standard.phenology_params or {}
    if standard.ndvi_curve:
        phenology_params["ndvi_curve"] = standard.ndvi_curve
    if standard.lst_curve:
        phenology_params["lst_curve"] = standard.lst_curve

    # 创建金标准
    new_standard = GoldenStandard(
        id=standard_id,
        user_id=current_user.id,
        project_id=active_project.id if active_project else None,
        model_name=standard.model_name,
        crop_type=standard.crop_type,
        latitude=standard.latitude,
        longitude=standard.longitude,
        location_description=standard.location_description,
        suitability_params=standard.suitability_params,
        phenology_params=phenology_params if phenology_params else None,
        description=standard.description,
        source=standard.source,
        tags=standard.tags,
    )

    db.add(new_standard)
    db.commit()
    db.refresh(new_standard)

    return new_standard


@router.put("/{standard_id}", response_model=GoldenStandardSchema)
def update_standard(
    standard_id: str,
    update: GoldenStandardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新金标准信息
    """
    standard = db.query(GoldenStandard).filter(
        GoldenStandard.id == standard_id
    ).first()

    if not standard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="金标准不存在"
        )

    # 权限检查
    if standard.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此金标准"
        )

    # 更新字段
    if update.model_name is not None:
        standard.model_name = update.model_name
    if update.location_description is not None:
        standard.location_description = update.location_description
    if update.suitability_params is not None:
        standard.suitability_params = update.suitability_params
    if update.phenology_params is not None:
        standard.phenology_params = update.phenology_params
    if update.description is not None:
        standard.description = update.description
    if update.source is not None:
        standard.source = update.source
    if update.tags is not None:
        standard.tags = update.tags

    db.commit()
    db.refresh(standard)

    return standard


@router.post("/{standard_id}/rename", response_model=MessageResponse)
def rename(
    standard_id: str,
    body: GoldenStandardRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    重命名金标准（兼容旧版 API）
    """
    name = (body.new_name or "").strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new_name cannot be empty"
        )

    standard = db.query(GoldenStandard).filter(
        GoldenStandard.id == standard_id
    ).first()

    if not standard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="金标准不存在"
        )

    # 权限检查
    if standard.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此金标准"
        )

    standard.model_name = name
    db.commit()

    return MessageResponse(
        message="重命名成功",
        detail=f"金标准已重命名为 '{name}'"
    )


@router.delete("/{standard_id}", response_model=MessageResponse)
def delete(
    standard_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除金标准（软删除）
    """
    standard = db.query(GoldenStandard).filter(
        GoldenStandard.id == standard_id
    ).first()

    if not standard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="金标准不存在"
        )

    # 权限检查
    if standard.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此金标准"
        )

    # 软删除
    standard.is_deleted = True
    db.commit()

    return MessageResponse(
        message="删除成功",
        detail=f"金标准 '{standard.model_name}' 已标记为删除"
    )
