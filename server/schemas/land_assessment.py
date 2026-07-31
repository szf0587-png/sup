"""土地资源评估 Pydantic 模型"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AccessibilityLayerRequest(BaseModel):
    """可达性图层配置"""

    datasource_name: str = Field(..., description="iServer 数据源名称")
    dataset_name: str = Field(..., description="iServer 数据集名称")
    label: Optional[str] = Field(None, description="图层标签")
    kind: Literal["road", "facility", "water", "other"] = Field("road", description="图层类型")
    weight: float = Field(1.0, ge=0, description="图层权重")


class LandAssessmentRequest(BaseModel):
    """土地资源评估请求"""

    boundary: Dict[str, Any] = Field(..., description="GeoJSON Polygon / MultiPolygon")
    project_id: Optional[str] = Field(None, description="项目ID")
    target_use: str = Field("general", description="目标用途: general/agriculture/construction/ecology")
    buffer_distance_m: float = Field(1000, ge=0, description="缓冲距离（米）")
    use_3d: bool = Field(True, description="是否启用 3D 资源检查")
    scene_name: Optional[str] = Field(None, description="指定三维场景名称")
    constraint_datasets: Optional[List[str]] = Field(
        None,
        description="约束图层名称列表",
    )
    accessibility_layers: Optional[List[AccessibilityLayerRequest]] = Field(
        None,
        description="可达性分析图层配置",
    )
    weights: Optional[Dict[str, float]] = Field(
        None,
        description="评分权重",
    )


class AssessmentFactor(BaseModel):
    """单个评估因子"""

    name: str
    score: float
    weight: float
    source: str
    note: Optional[str] = None


class LayerSummary(BaseModel):
    """图层统计摘要"""

    name: str
    label: Optional[str] = None
    score: float
    source: str
    feature_count: Optional[int] = None
    note: Optional[str] = None


class LandAssessmentResponse(BaseModel):
    """土地资源评估响应"""

    run_id: str
    status: str
    data_mode: str
    project_id: Optional[str]
    target_use: str
    overall_score: float
    grade: str
    decision: str
    summary: str
    factors: List[AssessmentFactor]
    spatial: Dict[str, Any]
    three_d: Dict[str, Any]
    recommendations: List[str]
    visualization: Dict[str, Any]
    report_path: Optional[str] = None
