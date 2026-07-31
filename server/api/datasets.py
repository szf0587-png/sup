"""数据集管理 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from pathlib import Path
import uuid

from server.database import get_db
from server.models.user import User
from server.models.dataset import Dataset
from server.schemas.dataset import (
    DatasetUploadResponse,
    DatasetListResponse,
    DatasetListItem,
    DatasetDetailResponse,
    DatasetUpdateRequest,
)
from server.schemas.auth import MessageResponse
from server.middleware.auth import get_current_user, require_admin
from server.config import DATA_DIR
from server.utils.file_upload import (
    save_uploaded_file,
    extract_vector_metadata,
    extract_raster_metadata,
    extract_geojson_metadata,
    detect_dataset_type,
    get_file_extension,
)

router = APIRouter(prefix="/api/datasets", tags=["数据集管理"])


@router.post("/upload", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(..., description="上传的数据文件"),
    name: Optional[str] = Form(None, description="数据集名称（可选，默认使用文件名）"),
    description: Optional[str] = Form(None, description="数据集描述"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传数据集文件

    支持的格式：
    - 矢量数据：GeoJSON (.geojson, .json), Shapefile (.shp), KML (.kml)
    - 栅格数据：GeoTIFF (.tif, .tiff), IMG (.img)

    自动提取元数据（CRS、边界、字段信息等）
    """
    # 读取文件内容
    file_content = await file.read()

    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件内容为空"
        )

    # 检测数据集类型
    dataset_type = detect_dataset_type(file.filename)

    # 保存文件
    try:
        relative_path, file_size = save_uploaded_file(
            file_content=file_content,
            filename=file.filename,
            user_id=current_user.id,
            dataset_type=dataset_type,
            base_dir=Path(DATA_DIR)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
        )

    # 获取绝对路径用于元数据提取
    absolute_path = Path(DATA_DIR) / relative_path

    # 提取元数据
    crs = None
    bounds = None
    extra_metadata = {}

    file_ext = get_file_extension(file.filename)

    if dataset_type == "vector":
        if file_ext in ['.geojson', '.json']:
            metadata = extract_geojson_metadata(absolute_path)
        else:
            metadata = extract_vector_metadata(absolute_path)

        crs = metadata.get('crs')
        bounds = metadata.get('bounds')
        extra_metadata = {
            'fields': metadata.get('fields', []),
            'feature_count': metadata.get('feature_count'),
            'geometry_type': metadata.get('geometry_type'),
            'error': metadata.get('error')
        }

    elif dataset_type == "raster":
        metadata = extract_raster_metadata(absolute_path)
        crs = metadata.get('crs')
        bounds = metadata.get('bounds')
        extra_metadata = {
            'bands': metadata.get('bands', []),
            'width': metadata.get('width'),
            'height': metadata.get('height'),
            'band_count': metadata.get('band_count'),
            'nodata': metadata.get('nodata'),
            'error': metadata.get('error')
        }

    # 创建数据集记录
    dataset_id = f"dataset_{uuid.uuid4().hex[:12]}"
    dataset_name = name or Path(file.filename).stem

    new_dataset = Dataset(
        id=dataset_id,
        user_id=current_user.id,
        name=dataset_name,
        description=description,
        dataset_type=dataset_type,
        file_path=relative_path,
        file_size=file_size,
        crs=crs,
        bounds=bounds,
        extra_metadata=extra_metadata,
    )

    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)

    return new_dataset


@router.get("", response_model=DatasetListResponse)
def list_datasets(
    dataset_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    列出当前用户的所有数据集

    参数：
    - dataset_type: 可选，筛选数据集类型 (vector/raster/gee)
    """
    query = db.query(Dataset).filter(
        Dataset.user_id == current_user.id,
        Dataset.is_deleted == False
    )

    if dataset_type:
        query = query.filter(Dataset.dataset_type == dataset_type)

    datasets = query.order_by(Dataset.created_at.desc()).all()

    return DatasetListResponse(
        total=len(datasets),
        datasets=[DatasetListItem.model_validate(ds) for ds in datasets]
    )


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取数据集详情

    只能访问自己的数据集（管理员可以访问所有数据集）
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在"
        )

    # 权限检查：只能访问自己的数据集（管理员除外）
    if dataset.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此数据集"
        )

    return dataset


@router.put("/{dataset_id}", response_model=DatasetDetailResponse)
def update_dataset(
    dataset_id: str,
    request: DatasetUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新数据集信息（名称、描述）
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在"
        )

    # 权限检查
    if dataset.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此数据集"
        )

    # 更新字段
    if request.name is not None:
        dataset.name = request.name
    if request.description is not None:
        dataset.description = request.description

    db.commit()
    db.refresh(dataset)

    return dataset


@router.delete("/{dataset_id}", response_model=MessageResponse)
def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除数据集（软删除）

    只标记为已删除，不实际删除文件
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在"
        )

    # 权限检查
    if dataset.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此数据集"
        )

    # 软删除
    dataset.is_deleted = True
    db.commit()

    return MessageResponse(
        message="数据集已删除",
        detail=f"数据集 '{dataset.name}' 已标记为删除"
    )


@router.get("/admin/all", response_model=DatasetListResponse)
def list_all_datasets(
    dataset_type: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    管理员：列出所有用户的数据集

    需要管理员权限
    """
    query = db.query(Dataset).filter(Dataset.is_deleted == False)

    if dataset_type:
        query = query.filter(Dataset.dataset_type == dataset_type)

    datasets = query.order_by(Dataset.created_at.desc()).all()

    return DatasetListResponse(
        total=len(datasets),
        datasets=[DatasetListItem.model_validate(ds) for ds in datasets]
    )
