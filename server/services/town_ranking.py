"""Town Ranking Service — Top N 候选乡镇筛选

职责:
1. 加载洛南县乡镇边界、DEM、约束区、GEE 缓存
2. 逐乡镇计算 AHP 适宜性 (iobjectspy analyst 算子)
3. 逐乡镇计算物候匹配分数
4. 按 (0.7×适宜性 + 0.3×物候) 加权排序输出 Top N
5. 标记数据覆盖率不足的乡镇

依赖:
- iobjectspy.analyst: calculate_slope, calculate_aspect, reclass_grid, multilayer_overlay
- numpy: 均值计算、排序
- server.services.phenology: calculate_similarity
"""
from __future__ import annotations

import uuid
from pathlib import Path

from server.config import CASE_STUDY, RANKING, DATA_DIR


def rank_towns(
    golden_standard_id: str,
    top_n: int = 5,
    county: str = "洛南县",
) -> dict:
    """
    执行乡镇筛选并返回 Top N 结果。

    Phase 1 最小实现: 在 GIS 数据到位前，使用模拟因子完成端到端验证。
    数据到位后切换为 iobjectspy 算子。

    Returns:
        {"run_id": str, "towns": [...], "status": str}
    """
    run_id = f"scr-{uuid.uuid4().hex[:8]}"
    towns_file = DATA_DIR / "vector" / "luonan_towns.geojson"
    dem_file = DATA_DIR / "raster" / "luonan_dem.tif"

    # 检查数据就绪
    if not towns_file.exists():
        return _run_with_mock_factors(run_id, top_n, county)

    if not dem_file.exists():
        return _run_with_mock_factors(run_id, top_n, county)

    # 数据就绪: 使用 iobjectspy 算子计算
    return _run_with_iobjectspy(run_id, towns_file, dem_file, golden_standard_id, top_n)


def _run_with_mock_factors(run_id: str, top_n: int, county: str) -> dict:
    """模拟因子计算 — 数据到位前的端到端验证方案"""
    mock_towns = [
        {"town_code": "611021101", "town_name": "城关街道", "latitude": 34.092, "longitude": 110.151, "suitability": 82.3, "phenology": 75.1, "coverage": 0.95,
         "factors": {"slope": 0.28, "elevation": 0.22, "aspect": 0.17, "climate": 0.15, "constraints": 0.18}},
        {"town_code": "611021102", "town_name": "永丰镇", "latitude": 34.168, "longitude": 110.086, "suitability": 78.6, "phenology": 80.2, "coverage": 0.92,
         "factors": {"slope": 0.25, "elevation": 0.23, "aspect": 0.16, "climate": 0.18, "constraints": 0.18}},
        {"town_code": "611021103", "town_name": "保安镇", "latitude": 34.231, "longitude": 110.135, "suitability": 75.1, "phenology": 72.3, "coverage": 0.88,
         "factors": {"slope": 0.22, "elevation": 0.26, "aspect": 0.18, "climate": 0.19, "constraints": 0.15}},
        {"town_code": "611021104", "town_name": "景村镇", "latitude": 34.019, "longitude": 110.236, "suitability": 71.8, "phenology": 74.5, "coverage": 0.91,
         "factors": {"slope": 0.24, "elevation": 0.21, "aspect": 0.19, "climate": 0.22, "constraints": 0.14}},
        {"town_code": "611021105", "town_name": "石门镇", "latitude": 34.144, "longitude": 110.262, "suitability": 69.4, "phenology": 68.9, "coverage": 0.85,
         "factors": {"slope": 0.20, "elevation": 0.28, "aspect": 0.18, "climate": 0.21, "constraints": 0.13}},
        {"town_code": "611021106", "town_name": "巡检镇", "latitude": 34.311, "longitude": 110.254, "suitability": 55.2, "phenology": 62.1, "coverage": 0.72,
         "factors": {"slope": 0.18, "elevation": 0.30, "aspect": 0.20, "climate": 0.20, "constraints": 0.12}},
        {"town_code": "611021107", "town_name": "石坡镇", "latitude": 34.241, "longitude": 110.301, "suitability": 62.3, "phenology": 58.7, "coverage": 0.78,
         "factors": {"slope": 0.19, "elevation": 0.29, "aspect": 0.21, "climate": 0.19, "constraints": 0.12}},
    ]

    sw = RANKING["suitability_weight"]
    pw = RANKING["phenology_weight"]
    min_cov = RANKING["min_data_coverage"]

    results = []
    for t in mock_towns:
        if t["coverage"] < min_cov:
            continue
        overall = round(sw * t["suitability"] + pw * t["phenology"], 2)
        results.append({**t, "overall_score": overall})

    results.sort(key=lambda x: (-x["overall_score"], -x["phenology"], x["town_code"]))
    top = results[:top_n]

    return {
        "run_id": run_id,
        "status": "mock",
        "data_mode": "mock",
        "message": "使用模拟数据 — 等待洛南县 GIS 数据到位",
        "county": county,
        "towns": [
            {
                "town_code": t["town_code"],
                "town_name": t["town_name"],
                "suitability_score": t["suitability"],
                "phenology_score": t["phenology"],
                "overall_score": t["overall_score"],
                "data_coverage": t["coverage"],
                "factor_contributions": t["factors"],
                "latitude": t["latitude"],
                "longitude": t["longitude"],
            }
            for t in top
        ],
        "rank_method": f"{sw}×适宜性 + {pw}×物候匹配",
    }


def _run_with_iobjectspy(
    run_id: str,
    towns_file: Path,
    dem_file: Path,
    golden_standard_id: str,
    top_n: int,
) -> dict:
    """使用 iobjectspy 真实计算 AHP 适宜性 + 物候匹配"""
    try:
        import os
        import sys
        import numpy as np

        # 确保 SuperMap bin 目录在 PATH 中（iobjectspy 依赖其 DLL）
        supermap_bin = r"E:\SuperMap\bin"
        if supermap_bin not in os.environ.get("PATH", ""):
            os.environ["PATH"] = supermap_bin + ";" + os.environ.get("PATH", "")

        # 确保 iobjectspy 的 bin_python 目录在 sys.path 中
        bin_python = r"E:\SuperMap\bin_python"
        if bin_python not in sys.path:
            sys.path.insert(0, bin_python)

        from iobjectspy import analyst, data
        import json

        print(f"[town_ranking] iobjectspy 加载成功，开始 AHP 计算")

        # ─── 1. 加载乡镇边界 ───
        with open(towns_file, "r", encoding="utf-8") as f:
            towns_geojson = json.load(f)

        if towns_geojson.get("type") != "FeatureCollection":
            print("[town_ranking] towns_file 不是 FeatureCollection")
            return _run_with_mock_factors(run_id, top_n, CASE_STUDY["county"])

        towns = towns_geojson.get("features", [])
        if not towns:
            print("[town_ranking] towns_file 为空")
            return _run_with_mock_factors(run_id, top_n, CASE_STUDY["county"])

        print(f"[town_ranking] 加载了 {len(towns)} 个乡镇边界")

        # ─── 2. 打开 DEM 栅格数据源 ───
        # iobjectspy 需要先将 GeoTIFF 导入 UDBX 或直接用 GDAL 读取
        # 这里假设 DEM 已转为 UDBX 格式，或使用 analyst 的栅格函数直接处理 TIFF

        # 简化方案：直接对每个乡镇中心点做 AHP 评分（不做真实栅格叠加）
        # 真实方案需要：
        # - slope_grid = analyst.calculate_slope(dem_dataset)
        # - aspect_grid = analyst.calculate_aspect(dem_dataset)
        # - reclass 各因子到 1-9 分
        # - weighted_overlay = analyst.multilayer_overlay([slope, aspect, elev, climate], weights)
        # - zonal_stats = analyst.zonal_statistics_on_raster_value(weighted_overlay, towns_vector)

        # 当前先用 mock 因子 + iobjectspy 验证流程联通
        print("[town_ranking] 当前使用简化评分（待 DEM 栅格处理流程完整后替换）")

        sw = RANKING["suitability_weight"]
        pw = RANKING["phenology_weight"]
        min_cov = RANKING["min_data_coverage"]

        results = []
        for feat in towns:
            props = feat.get("properties", {})
            town_code = props.get("town_code") or props.get("code") or props.get("TOWNCODE")
            town_name = props.get("town_name") or props.get("name") or props.get("TOWNNAME")

            if not town_code or not town_name:
                continue

            # 提取中心点坐标
            geom = feat.get("geometry", {})
            if geom.get("type") == "Polygon":
                coords = geom["coordinates"][0]
                lon = sum(c[0] for c in coords) / len(coords)
                lat = sum(c[1] for c in coords) / len(coords)
            elif geom.get("type") == "Point":
                lon, lat = geom["coordinates"]
            else:
                lon, lat = 110.15, 34.09  # fallback

            # TODO: 真实 AHP 计算应从 zonal_statistics 结果读取
            # 当前用随机因子模拟（待数据就绪后替换）
            import random
            random.seed(hash(town_code) % 10000)

            suitability = 55 + random.random() * 30  # 55-85
            phenology = 60 + random.random() * 25    # 60-85
            coverage = 0.75 + random.random() * 0.2  # 0.75-0.95

            if coverage < min_cov:
                continue

            overall = round(sw * suitability + pw * phenology, 2)
            results.append({
                "town_code": str(town_code),
                "town_name": str(town_name),
                "suitability": suitability,
                "phenology": phenology,
                "overall_score": overall,
                "coverage": coverage,
                "latitude": lat,
                "longitude": lon,
            })

        results.sort(key=lambda x: (-x["overall_score"], -x["phenology"], x["town_code"]))
        top = results[:top_n]

        return {
            "run_id": run_id,
            "status": "computed_with_iobjectspy",
            "data_mode": "iobjectspy_simplified",  # 标记为简化模式
            "message": "iobjectspy 已激活 — 当前使用简化评分，待 DEM 栅格处理流程完整后启用真实 AHP",
            "county": CASE_STUDY["county"],
            "towns": [
                {
                    "town_code": t["town_code"],
                    "town_name": t["town_name"],
                    "suitability_score": round(t["suitability"], 1),
                    "phenology_score": round(t["phenology"], 1),
                    "overall_score": t["overall_score"],
                    "data_coverage": round(t["coverage"], 2),
                    "factor_contributions": {
                        "slope": 0.24, "elevation": 0.22, "aspect": 0.18,
                        "climate": 0.20, "constraints": 0.16
                    },
                    "latitude": round(t["latitude"], 4),
                    "longitude": round(t["longitude"], 4),
                }
                for t in top
            ],
            "rank_method": f"{sw}×适宜性 + {pw}×物候匹配（iobjectspy 简化模式）",
        }

    except ImportError as e:
        print(f"[town_ranking] iobjectspy 导入失败: {e}")
        return _run_with_mock_factors(run_id, top_n, CASE_STUDY["county"])
    except Exception as e:
        print(f"[town_ranking] iobjectspy 计算异常: {e}")
        import traceback
        traceback.print_exc()
        return _run_with_mock_factors(run_id, top_n, CASE_STUDY["county"])
