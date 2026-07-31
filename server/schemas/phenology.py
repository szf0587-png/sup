"""物候匹配 Pydantic 模型"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class PhenologyRequest(BaseModel):
    lat: float
    lon: float


class PhenologyMatchRequest(BaseModel):
    """物候匹配请求"""
    lat: float
    lon: float
    golden_standard_id: Optional[str] = None
    search_radius_km: float = 50.0
    sample_points: int = 20
    sample_resolution_m: int = 1000
    top_n: int = 5
    year: int = 2020


class PhenologyMatchResult(BaseModel):
    """对单个金标准的匹配结果"""
    golden_standard_id: str
    golden_standard_name: str
    similarity_score: float
    ndvi_correlation: float
    lst_correlation: float
    slope_similarity: float
    milestones_match: Dict[str, Any]


class PhenologySamplePlot(BaseModel):
    """采样点"""
    lat: float
    lon: float
    similarity_score: float
    matched_standard_id: str
    matched_standard_name: str
    ndvi_correlation: float
    lst_correlation: float
    slope_similarity: float


class PhenologyMatchResponse(BaseModel):
    """物候匹配完整响应"""
    status: str
    data_source: str = "simulated"
    gee_available: bool = False
    gee_message: Optional[str] = None
    local_lat: float
    local_lon: float
    local_ndvi: List[float]
    local_lst: List[float]
    best_golden_ndvi: Optional[List[float]] = None
    best_golden_lst: Optional[List[float]] = None
    matches: List[PhenologyMatchResult]
    sampled_matches: List[PhenologySamplePlot] = []
