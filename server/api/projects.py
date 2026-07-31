"""项目管理 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from server.database import get_db
from server.models.user import User
from server.models.project import Project
from server.models.dataset import Dataset
from server.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectAddDatasetRequest,
    ProjectListResponse,
    ProjectListItem,
    ProjectDetailResponse,
    ProjectActivateResponse,
)
from server.schemas.auth import MessageResponse
from server.middleware.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/projects", tags=["项目管理"])


@router.post("", response_model=ProjectDetailResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    request: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新项目

    每个用户可以创建多个项目，但同时只能激活一个项目
    """
    # 生成项目 ID
    project_id = f"project_{uuid.uuid4().hex[:12]}"

    # 检查是否是用户的第一个项目，如果是则自动激活
    existing_projects = db.query(Project).filter(
        Project.user_id == current_user.id,
        Project.is_deleted == False
    ).count()

    is_active = (existing_projects == 0)

    # 创建项目
    new_project = Project(
        id=project_id,
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        region=request.region,
        config={},
        dataset_ids=[],
        is_active=is_active,
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


@router.get("", response_model=ProjectListResponse)
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    列出当前用户的所有项目
    """
    projects = db.query(Project).filter(
        Project.user_id == current_user.id,
        Project.is_deleted == False
    ).order_by(Project.updated_at.desc()).all()

    # 查找激活的项目
    active_project = db.query(Project).filter(
        Project.user_id == current_user.id,
        Project.is_active == True,
        Project.is_deleted == False
    ).first()

    # 计算每个项目的数据集数量
    project_items = []
    for project in projects:
        dataset_count = len(project.dataset_ids) if project.dataset_ids else 0
        item = ProjectListItem(
            id=project.id,
            name=project.name,
            description=project.description,
            is_active=project.is_active,
            dataset_count=dataset_count,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        project_items.append(item)

    return ProjectListResponse(
        total=len(projects),
        active_project_id=active_project.id if active_project else None,
        projects=project_items
    )


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取项目详情

    只能访问自己的项目（管理员可以访问所有项目）
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 权限检查
    if project.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此项目"
        )

    return project


@router.put("/{project_id}", response_model=ProjectDetailResponse)
def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新项目信息
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 权限检查
    if project.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此项目"
        )

    # 更新字段
    if request.name is not None:
        project.name = request.name
    if request.description is not None:
        project.description = request.description
    if request.region is not None:
        project.region = request.region
    if request.config is not None:
        project.config = request.config

    db.commit()
    db.refresh(project)

    return project


@router.post("/{project_id}/activate", response_model=ProjectActivateResponse)
def activate_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    激活项目

    同一时间只能有一个激活的项目，激活新项目会自动取消之前激活的项目
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 权限检查
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权激活此项目"
        )

    # 取消当前用户的其他激活项目
    db.query(Project).filter(
        Project.user_id == current_user.id,
        Project.is_active == True
    ).update({"is_active": False})

    # 激活目标项目
    project.is_active = True
    db.commit()

    return ProjectActivateResponse(
        message="项目已激活",
        active_project_id=project.id,
        active_project_name=project.name
    )


@router.post("/{project_id}/datasets", response_model=ProjectDetailResponse)
def add_dataset_to_project(
    project_id: str,
    request: ProjectAddDatasetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    将数据集添加到项目

    只能添加自己的数据集
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 权限检查
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此项目"
        )

    # 检查数据集是否存在且属于当前用户
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在"
        )

    if dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权使用此数据集"
        )

    # 添加数据集到项目
    if project.dataset_ids is None:
        project.dataset_ids = []

    if request.dataset_id not in project.dataset_ids:
        project.dataset_ids.append(request.dataset_id)
        # 手动标记为已修改（SQLAlchemy 对 JSON 字段需要显式标记）
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(project, "dataset_ids")

        db.commit()
        db.refresh(project)

    return project


@router.delete("/{project_id}/datasets/{dataset_id}", response_model=ProjectDetailResponse)
def remove_dataset_from_project(
    project_id: str,
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    从项目中移除数据集
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 权限检查
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此项目"
        )

    # 移除数据集
    if project.dataset_ids and dataset_id in project.dataset_ids:
        project.dataset_ids.remove(dataset_id)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(project, "dataset_ids")

        db.commit()
        db.refresh(project)

    return project


@router.delete("/{project_id}", response_model=MessageResponse)
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除项目（软删除）

    删除激活的项目后，会自动激活最近更新的项目
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )

    # 权限检查
    if project.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此项目"
        )

    was_active = project.is_active

    # 软删除
    project.is_deleted = True
    project.is_active = False
    db.commit()

    # 如果删除的是激活项目，自动激活最近的项目
    if was_active:
        latest_project = db.query(Project).filter(
            Project.user_id == current_user.id,
            Project.is_deleted == False
        ).order_by(Project.updated_at.desc()).first()

        if latest_project:
            latest_project.is_active = True
            db.commit()

    return MessageResponse(
        message="项目已删除",
        detail=f"项目 '{project.name}' 已标记为删除"
    )
