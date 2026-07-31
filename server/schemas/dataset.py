"""数据集相关的 Pydantic 模型"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DatasetUploadResponse(BaseModel):
    """数据集上传响应"""
    id: str
    name: str
    dataset_type: str
    file_path: str
    file_size: int
    crs: Optional[str]
    bounds: Optional[List[float]]
    extra_metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetListItem(BaseModel):
    """数据集列表项"""
    id: str
    name: str
    description: Optional[str]
    dataset_type: str
    file_size: Optional[int]
    crs: Optional[str]
    bounds: Optional[List[float]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetDetailResponse(BaseModel):
    """数据集详情响应"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    dataset_type: str
    file_path: str
    file_size: Optional[int]
    crs: Optional[str]
    bounds: Optional[List[float]]
    extra_metadata: Optional[Dict[str, Any]]
    iserver_service_id: Optional[str]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetUpdateRequest(BaseModel):
    """数据集更新请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="数据集名称")
    description: Optional[str] = Field(None, description="数据集描述")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "更新后的数据集名称",
                "description": "更新后的描述"
            }
        }


class DatasetListResponse(BaseModel):
    """数据集列表响应"""
    total: int
    datasets: List[DatasetListItem]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "datasets": [
                    {
                        "id": "dataset_abc123",
                        "name": "洛南县行政区划",
                        "description": "洛南县乡镇边界数据",
                        "dataset_type": "vector",
                        "file_size": 1024000,
                        "crs": "EPSG:4326",
                        "bounds": [109.0, 33.0, 110.0, 34.0],
                        "created_at": "2026-07-26T10:00:00",
                        "updated_at": "2026-07-26T10:00:00"
                    }
                ]
            }
        }
