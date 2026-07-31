"""大棚检测服务 — YOLO 推理 + 地理化 + 离线降级"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from server.config import DATA_DIR


def detect_greenhouses(
    image_path: Path,
    model_path: Optional[Path] = None,
    confidence: float = 0.5,
) -> dict:
    """
    在大幅高分影像上执行大棚检测。

    Phase 2 最小实现: 返回预计算结果或模拟数据。
    实时推理在 YOLO 模型和环境就绪后启用。

    Returns:
        {
            "status": "ok"|"precomputed"|"simulated",
            "features": [...],  # GeoJSON FeatureCollection
            "count": int,
            "area_ha": float,
        }
    """
    # 1. 尝试预计算结果
    cache_key = image_path.stem
    precomputed = DATA_DIR / "snapshots" / f"facilities_{cache_key}.json"
    if precomputed.exists():
        with open(precomputed, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["status"] = "precomputed"
        return data

    # 2. 尝试实时推理
    if model_path and model_path.exists():
        try:
            return _run_inference(image_path, model_path, confidence)
        except Exception as e:
            print(f"[greenhouse] Real-time inference failed: {e}")

    # 3. 降级: 模拟结果
    return _simulated_result()


def _run_inference(image_path: Path, model_path: Path, confidence: float) -> dict:
    """真实 YOLO 推理（环境就绪后启用）"""
    # TODO: 接入 YOLOv8 模型
    # from ultralytics import YOLO
    # model = YOLO(str(model_path))
    # results = model(str(image_path), conf=confidence)
    # ... 地理化: 像素坐标 → 地理坐标 (仿射变换)
    return {"status": "inference_not_configured", "features": [], "count": 0, "area_ha": 0.0}


def _simulated_result() -> dict:
    """模拟大棚检测结果（用于端到端验证）"""
    return {
        "status": "simulated",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [110.15, 34.09], [110.152, 34.09],
                        [110.152, 34.092], [110.15, 34.092],
                        [110.15, 34.09],
                    ]],
                },
                "properties": {"id": 1, "confidence": 0.92, "area_m2": 1200.0},
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [110.155, 34.095], [110.158, 34.095],
                        [110.158, 34.097], [110.155, 34.097],
                        [110.155, 34.095],
                    ]],
                },
                "properties": {"id": 2, "confidence": 0.88, "area_m2": 1800.0},
            },
        ],
        "count": 2,
        "area_ha": 0.30,
    }


def georeference_detections(
    detections: list[dict],
    geotransform: tuple,
    crs: str = "EPSG:4326",
) -> list[dict]:
    """
    将像素坐标的检测框转换为地理坐标 GeoJSON features。

    geotransform: (origin_x, pixel_width, 0, origin_y, 0, -pixel_height)
    """
    features = []
    for i, det in enumerate(detections):
        x1, y1, x2, y2 = det["bbox"]  # pixel coords
        lon1 = geotransform[0] + x1 * geotransform[1]
        lat1 = geotransform[3] + y1 * geotransform[5]
        lon2 = geotransform[0] + x2 * geotransform[1]
        lat2 = geotransform[3] + y2 * geotransform[5]

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon1, lat1], [lon2, lat1],
                    [lon2, lat2], [lon1, lat2],
                    [lon1, lat1],
                ]],
            },
            "properties": {
                "id": i + 1,
                "confidence": det.get("confidence", 0.0),
                "area_m2": abs((lon2 - lon1) * (lat2 - lat1) * 111000 * 111000),
            },
        })
    return features
