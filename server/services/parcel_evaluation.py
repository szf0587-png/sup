"""地块精评服务 — AHP 适宜性 + 物候 + 空间约束 + 设施证据整合"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from server.config import DATA_DIR, GOLDEN_STANDARDS_FILE
from server.services.phenology import calculate_similarity


def evaluate_parcel(
    town_code: str,
    parcel_geojson: dict,
    golden_standard_id: str,
) -> dict:
    """
    对指定地块执行综合评价，返回评分、物候、约束和设施证据。

    Phase 2 最小实现: 使用模拟数据，GIS 数据到位后接入 iobjectspy AHP。
    """
    run_id = f"par-{uuid.uuid4().hex[:8]}"

    # 1. AHP 适宜性 (模拟)
    ahp = _evaluate_ahp(parcel_geojson)

    # 2. 物候匹配 (从金标准库读取曲线)
    phenology = _evaluate_phenology(parcel_geojson, golden_standard_id)

    # 3. 空间约束
    from server.services.spatial_analysis import compute_buffer_stats, overlay_constraint_stats
    buffer = compute_buffer_stats(
        geometry=parcel_geojson.get("geometry", {}),
        buffer_distance=500,
    )
    constraints = overlay_constraint_stats(parcel_geojson)

    # 4. 设施证据
    facilities = _get_facility_evidence(town_code)

    # 5. 加权汇总
    overall = round(
        0.40 * ahp["score"]
        + 0.30 * phenology["similarity_score"]
        + 0.15 * (100 - constraints.get("constraint_ratio", 0) * 100)
        + 0.15 * facilities.get("density_score", 50),
        2,
    )

    return {
        "run_id": run_id,
        "town_code": town_code,
        "overall_score": overall,
        "ahp": ahp,
        "phenology": phenology,
        "spatial": {"buffer": buffer, "constraints": constraints},
        "facilities": facilities,
        "grade": _to_grade(overall),
    }


def _evaluate_ahp(parcel_geojson: dict) -> dict:
    """AHP 适宜性评价（模拟）"""
    return {
        "score": 78.5,
        "factors": {
            "slope": {"score": 8.2, "weight": 0.35},
            "elevation": {"score": 7.8, "weight": 0.25},
            "aspect": {"score": 7.5, "weight": 0.20},
            "climate": {"score": 6.9, "weight": 0.20},
        },
        "source": "simulated",
    }


def _evaluate_phenology(parcel_geojson: dict, golden_standard_id: str) -> dict:
    """物候匹配评价"""
    # 加载金标准曲线
    if GOLDEN_STANDARDS_FILE.exists():
        with open(GOLDEN_STANDARDS_FILE, "r", encoding="utf-8") as f:
            standards = json.load(f)
        gs = next((s for s in standards
                   if (s.get("id") or s.get("model_id")) == golden_standard_id), None)
        if gs:
            # 使用模拟本地曲线计算相似度
            import numpy as np
            local_ndvi = [0.2 + 0.6 * np.exp(-((d - 180) ** 2) / 2000) for d in range(365)]
            local_lst = [20 + 15 * np.sin(2 * np.pi * (d - 80) / 365) for d in range(365)]
            sim = calculate_similarity(local_ndvi, local_lst, gs["ndvi_curve"], gs["lst_curve"])
            return {**sim, "source": "simulated"}
    return {"similarity_score": 70.0, "source": "default"}


def _get_facility_evidence(town_code: str) -> dict:
    """设施证据（大棚检测结果）"""
    # 从预计算结果或快照读取
    snap = DATA_DIR / "snapshots" / f"facilities_{town_code}.json"
    if snap.exists():
        with open(snap, "r") as f:
            return json.load(f)
    return {
        "greenhouse_count": 12,
        "greenhouse_area_ha": 3.5,
        "density_score": 65.0,
        "source": "simulated",
    }


def _to_grade(score: float) -> str:
    if score >= 85:
        return "S"
    elif score >= 75:
        return "A"
    elif score >= 65:
        return "B"
    elif score >= 55:
        return "C"
    return "D"
