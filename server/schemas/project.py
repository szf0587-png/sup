"""项目相关的 Pydantic 模型"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProjectCreateRequest(BaseModel):
    """项目创建请求"""
    name: str = Field(..., min_length=1, max_length=255, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    region: Optional[Dict[str, Any]] = Field(None, description="研究区域边界（GeoJSON Polygon）")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "洛南县核桃适宜性分析",
                "description": "基于多源数据评估洛南县核桃种植适宜性",
                "region": {
                    "type": "Polygon",
                    "coordinates": [[[109.0, 33.0], [110.0, 33.0], [110.0, 34.0], [109.0, 34.0], [109.0, 33.0]]]
                }
            }
        }


class ProjectUpdateRequest(BaseModel):
    """项目更新请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    region: Optional[Dict[str, Any]] = Field(None, description="研究区域边界")
    config: Optional[Dict[str, Any]] = Field(None, description="项目配置")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "更新后的项目名称",
                "description": "更新后的描述",
                "config": {
                    "default_crs": "EPSG:4326",
                    "visualization": {
                        "base_color": "#2E7D32"
                    }
                }
            }
        }


class ProjectAddDatasetRequest(BaseModel):
    """项目添加数据集请求"""
    dataset_id: str = Field(..., description="数据集ID")

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": "dataset_abc123"
            }
        }


class ProjectListItem(BaseModel):
    """项目列表项"""
    id: str
    name: str
    description: Optional[str]
    is_active: bool
    dataset_count: int = Field(default=0, description="关联的数据集数量")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectDetailResponse(BaseModel):
    """项目详情响应"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    region: Optional[Dict[str, Any]]
    config: Optional[Dict[str, Any]]
    dataset_ids: Optional[List[str]]
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    total: int
    projects: List[ProjectListItem]
    active_project_id: Optional[str] = Field(None, description="当前激活的项目ID")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 3,
                "active_project_id": "project_abc123",
                "projects": [
                    {
                        "id": "project_abc123",
                        "name": "洛南县核桃适宜性分析",
                        "description": "基于多源数据评估",
                        "is_active": True,
                        "dataset_count": 5,
                        "created_at": "2026-07-26T10:00:00",
                        "updated_at": "2026-07-26T10:00:00"
                    }
                ]
            }
        }


class ProjectActivateResponse(BaseModel):
    """项目激活响应"""
    message: str
    active_project_id: str
    active_project_name: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "项目已激活",
                "active_project_id": "project_abc123",
                "active_project_name": "洛南县核桃适宜性分析"
            }
        }
