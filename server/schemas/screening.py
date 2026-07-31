"""区域筛选 Pydantic 模型"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ScreeningRequest(BaseModel):
    """区域筛选请求"""
    golden_standard_id: str
    county: str = "洛南县"
    top_n: int = 5


class TownResult(BaseModel):
    """单个乡镇筛选结果"""
    town_code: str
    town_name: str
    suitability_score: float
    phenology_score: float
    overall_score: float
    data_coverage: float
    factor_contributions: Dict[str, float]


class ScreeningResponse(BaseModel):
    """区域筛选完整响应"""
    run_id: str
    status: str
    county: str
    golden_standard_id: str
    golden_standard_name: str
    towns: List[TownResult]
    rank_method: str
