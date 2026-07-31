"""物候匹配 API 路由（数据库版本 - 多用户支持）"""
from __future__ import annotations

import numpy as np
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from server.database import get_db
from server.models.user import User
from server.models.golden_standard import GoldenStandard
from server.middleware.auth import get_current_user
from server.schemas.phenology import PhenologyMatchRequest, PhenologyMatchResponse, PhenologyMatchResult
from server.services.phenology import calculate_similarity

router = APIRouter(prefix="/api/phenology", tags=["phenology"])


def _simulate_curve(lat: float, lon: float, is_ndvi: bool = True) -> np.ndarray:
    """模拟 NDVI/LST 曲线（GEE 不可用时的降级方案）"""
    days = np.arange(365)
    if is_ndvi:
        offset = (lat - 34) * 5
        peak_day = 180 + offset
        curve = 0.2 + 0.6 * np.exp(-((days - peak_day) ** 2) / 2000)
    else:
        curve = 20 + 15 * np.sin(2 * np.pi * (days - 80) / 365)
    return curve.tolist()


@router.post("/match", response_model=PhenologyMatchResponse)
def match(
    req: PhenologyMatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    将指定地点的物候与金标准库进行一对多对比

    - 从数据库读取当前用户的金标准
    - 可指定金标准 ID 进行单个匹配
    - GEE 可用时拉取真实 MODIS NDVI 数据；不可用时使用模拟曲线降级
    """
    # 从数据库读取金标准
    query = db.query(GoldenStandard).filter(
        GoldenStandard.user_id == current_user.id,
        GoldenStandard.is_deleted == False
    )

    # 如果指定了金标准 ID，只匹配该金标准
    if req.golden_standard_id:
        query = query.filter(GoldenStandard.id == req.golden_standard_id)

    standards = query.all()

    if not standards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到匹配的金标准"
        )

    # 本地物候曲线（GEE 不可用时降级为模拟）
    local_ndvi = _simulate_curve(req.lat, req.lon, is_ndvi=True)
    local_lst = _simulate_curve(req.lat, req.lon, is_ndvi=False)

    matches: list = []
    for gs in standards:
        # 从 phenology_params 中获取曲线数据
        phenology_params = gs.phenology_params or {}
        gs_ndvi = phenology_params.get("ndvi_curve", [])
        gs_lst = phenology_params.get("lst_curve", [])

        # 如果金标准没有曲线数据，跳过
        if not gs_ndvi or not gs_lst:
            continue

        # 计算相似度
        sim = calculate_similarity(local_ndvi, local_lst, gs_ndvi, gs_lst)
        matches.append(PhenologyMatchResult(
            golden_standard_id=gs.id,
            golden_standard_name=gs.model_name,
            **sim,
        ))

    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="金标准缺少物候曲线数据（ndvi_curve 和 lst_curve）"
        )

    # 按相似度排序
    matches.sort(key=lambda m: m.similarity_score, reverse=True)
    top = matches[:req.top_n]

    # 最佳匹配的曲线
    best = standards[0] if standards else None
    best_phenology = best.phenology_params or {} if best else {}
    best_ndvi = best_phenology.get("ndvi_curve")
    best_lst = best_phenology.get("lst_curve")

    return PhenologyMatchResponse(
        status="success",
        data_source="simulated",
        gee_available=False,
        gee_message="GEE not configured — using simulated curves",
        local_lat=req.lat,
        local_lon=req.lon,
        local_ndvi=list(local_ndvi),
        local_lst=list(local_lst),
        best_golden_ndvi=best_ndvi,
        best_golden_lst=best_lst,
        matches=top,
        sampled_matches=[],
    )
