"""金标准 Pydantic 模型"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class GoldenStandardBase(BaseModel):
    model_name: str = Field(..., description="金标准名称")
    crop_type: str = Field(..., description="作物类型")
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")


class GoldenStandardCreate(GoldenStandardBase):
    """创建金标准请求"""
    location_description: Optional[str] = Field(None, description="位置描述")
    suitability_params: Optional[Dict[str, Any]] = Field(None, description="适宜性参数")
    phenology_params: Optional[Dict[str, Any]] = Field(None, description="物候参数")
    description: Optional[str] = Field(None, description="描述")
    source: Optional[str] = Field(None, description="数据来源")
    tags: Optional[List[str]] = Field(None, description="标签列表")

    # 兼容旧版本 API
    ndvi_curve: Optional[List[float]] = Field(None, description="NDVI曲线（兼容）")
    lst_curve: Optional[List[float]] = Field(None, description="LST曲线（兼容）")

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "洛南核桃最优模型",
                "crop_type": "核桃",
                "latitude": 34.09,
                "longitude": 110.15,
                "location_description": "洛南县古城镇",
                "suitability_params": {
                    "slope": {"min": 0, "max": 25},
                    "elevation": {"min": 800, "max": 1500},
                    "soil_ph": {"min": 6.5, "max": 7.5}
                },
                "phenology_params": {
                    "bud_break": "03-15",
                    "flowering": "04-20",
                    "harvest": "09-10"
                },
                "tags": ["高产", "优质", "示范点"]
            }
        }


class GoldenStandardUpdate(BaseModel):
    """更新金标准请求"""
    model_name: Optional[str] = None
    location_description: Optional[str] = None
    suitability_params: Optional[Dict[str, Any]] = None
    phenology_params: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None


class GoldenStandard(GoldenStandardBase):
    """金标准响应"""
    id: str
    user_id: str
    project_id: Optional[str]
    location_description: Optional[str]
    suitability_params: Optional[Dict[str, Any]]
    phenology_params: Optional[Dict[str, Any]]
    description: Optional[str]
    source: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GoldenStandardSummary(BaseModel):
    """下拉列表用的简化模型"""
    id: str
    model_name: str
    crop_type: str
    latitude: float
    longitude: float

    class Config:
        from_attributes = True


class GoldenStandardRename(BaseModel):
    new_name: str


class GoldenStandardListResponse(BaseModel):
    """金标准列表响应"""
    total: int
    standards: List[GoldenStandard]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 5,
                "standards": [
                    {
                        "id": "standard_abc123",
                        "user_id": "user_admin",
                        "project_id": "project_xyz",
                        "model_name": "洛南核桃最优模型",
                        "crop_type": "核桃",
                        "latitude": 34.09,
                        "longitude": 110.15,
                        "tags": ["高产", "优质"]
                    }
                ]
            }
        }

