"""GEE 客户端 — 数据拉取与本地缓存（真实 earthengine-api 集成）

支持从 Google Earth Engine 拉取 MODIS NDVI/LST 时序数据并缓存到本地。
"""
from __future__ import annotations

import json
from pathlib import Path


def get_cached_or_fetch(
    cache_dir: Path,
    image_id: str,
    region: dict,
    year: int = 2023,
    force_refresh: bool = False,
) -> Path | None:
    """
    从本地缓存读取 GEE 数据，缓存未命中时调用 earthengine-api 拉取。

    Args:
        cache_dir: 缓存目录（如 data/gee_cache）
        image_id: 影像集合 ID，如 "MODIS/061/MOD13Q1" (NDVI) 或 "MODIS/061/MOD11A2" (LST)
        region: GeoJSON 格式的 ROI 边界，如 {"type": "Point", "coordinates": [lon, lat]}
        year: 数据年份
        force_refresh: 强制重新拉取（忽略缓存）

    Returns:
        缓存文件路径（.json 格式），失败返回 None
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    # 缓存文件命名: image_id 的最后一段 + 年份 + 坐标 hash
    product_name = image_id.split("/")[-1]
    coord_hash = _hash_geometry(region)
    cache_file = cache_dir / f"{product_name}_{year}_{coord_hash}.json"

    if cache_file.exists() and not force_refresh:
        print(f"[gee_client] Cache hit: {cache_file.name}")
        return cache_file

    # 缓存未命中，尝试从 GEE 拉取
    print(f"[gee_client] Cache miss: {cache_file.name}")
    print(f"[gee_client] Fetching from GEE — {image_id}, year={year}, region={region}")

    try:
        import ee
        import os

        # 确保 GEE 已初始化
        if not _is_ee_initialized():
            project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
            if not project_id:
                print("[gee_client] GCP_PROJECT_ID 环境变量未设置，无法初始化 GEE")
                return None
            ee.Initialize(project=project_id)
            print(f"[gee_client] earthengine initialized with project={project_id}")

        # 构建 ROI（Point 转为小缓冲区，Polygon 直接用）
        if region["type"] == "Point":
            lon, lat = region["coordinates"]
            roi = ee.Geometry.Point([lon, lat]).buffer(500)  # 500m 缓冲区
        elif region["type"] == "Polygon":
            roi = ee.Geometry.Polygon(region["coordinates"])
        else:
            print(f"[gee_client] 不支持的几何类型: {region['type']}")
            return None

        # 构建时间范围（完整年度）
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        # 加载影像集合并过滤
        collection = (
            ee.ImageCollection(image_id)
            .filterDate(start_date, end_date)
            .filterBounds(roi)
        )

        # 提取时序：NDVI 或 LST
        band_name = _get_band_name(image_id)
        if not band_name:
            print(f"[gee_client] 无法识别产品的波段名: {image_id}")
            return None

        # 构建时间序列字典
        time_series = []
        img_list = collection.toList(collection.size())
        size = img_list.size().getInfo()

        if size == 0:
            print(f"[gee_client] 未找到数据: {image_id}, {year}, ROI={region}")
            return None

        print(f"[gee_client] 找到 {size} 幅影像，提取均值...")
        for i in range(size):
            img = ee.Image(img_list.get(i))
            date_str = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd").getInfo()
            stats = img.select(band_name).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=250,  # MODIS 250m 分辨率
                maxPixels=1e8,
            ).getInfo()

            value = stats.get(band_name)
            if value is not None:
                time_series.append({"date": date_str, "value": float(value)})

        if not time_series:
            print(f"[gee_client] 时序数据为空")
            return None

        # 写入缓存
        cache_data = {
            "image_id": image_id,
            "band": band_name,
            "year": year,
            "region": region,
            "time_series": time_series,
            "count": len(time_series),
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

        print(f"[gee_client] 已缓存 {len(time_series)} 条记录 → {cache_file.name}")
        return cache_file

    except ImportError:
        print("[gee_client] earthengine-api 未安装，请运行: pip install earthengine-api")
        return None
    except Exception as e:
        print(f"[gee_client] GEE 拉取失败: {e}")
        return None


def _is_ee_initialized() -> bool:
    """检查 earthengine 是否已初始化"""
    try:
        import ee
        ee.Number(1).getInfo()
        return True
    except Exception:
        return False


def _get_band_name(image_id: str) -> str | None:
    """根据影像集合 ID 返回目标波段名"""
    band_map = {
        "MOD13Q1": "NDVI",          # MODIS NDVI 16-day 250m
        "MYD13Q1": "NDVI",
        "MOD13A1": "NDVI",          # MODIS NDVI 16-day 500m
        "MOD11A2": "LST_Day_1km",   # MODIS LST 8-day 1km
        "MYD11A2": "LST_Day_1km",
        "MOD09A1": "sur_refl_b01",  # MODIS Surface Reflectance
    }
    for key, band in band_map.items():
        if key in image_id:
            return band
    return None


def _hash_geometry(region: dict) -> str:
    """对几何体坐标做简单 hash，用于缓存文件命名"""
    import hashlib
    coord_str = str(region.get("coordinates", ""))
    return hashlib.md5(coord_str.encode()).hexdigest()[:8]


def load_cached_time_series(cache_file: Path) -> list[dict] | None:
    """从缓存文件读取时序数据"""
    if not cache_file.exists():
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("time_series", [])
    except Exception as e:
        print(f"[gee_client] 缓存读取失败: {e}")
        return None
