"""天眼寻珍·苍穹 — 全局配置"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # src/tianyan-cangqiong
DATA_DIR = PROJECT_ROOT / "data"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TIANYAN_ROOT = Path(os.getenv("TIANYAN_ROOT", r"D:\Work space\天眼寻珍"))

# 固定案例数据
LUONAN_BOUNDARY = DATA_DIR / "luonan_boundary.geojson"
LUONAN_TOWNS = DATA_DIR / "luonan_towns.geojson"
LUONAN_DEM = DATA_DIR / "luonan_dem.tif"
LUONAN_CONSTRAINTS = DATA_DIR / "luonan_constraints.geojson"  # 禁建区、水体、建设用地
GEE_CACHE_DIR = DATA_DIR / "gee_cache"
GOLDEN_STANDARDS_FILE = DATA_DIR / "golden_standards.json"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
DATA_MANIFEST = DATA_DIR / "manifest.json"  # 数据台账

# ---------------------------------------------------------------------------
# 服务
# ---------------------------------------------------------------------------
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "127.0.0.1")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))

ISERVER_BASE = os.getenv("ISERVER_BASE", "http://127.0.0.1:8090")
ISERVER_USER = os.getenv("ISERVER_USER", "admin")
ISERVER_PASSWORD = os.getenv("ISERVER_PASSWORD", "")

# ---------------------------------------------------------------------------
# GEE
# ---------------------------------------------------------------------------
GEE_PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
USE_REAL_GEE = GEE_PROJECT_ID is not None

# ---------------------------------------------------------------------------
# 固定案例
# ---------------------------------------------------------------------------
CASE_STUDY = {
    "county": "洛南县",
    "city": "商洛市",
    "province": "陕西省",
    "center_lat": 34.09,
    "center_lon": 110.15,
    "default_crs": "EPSG:4326",
    "top_n_towns": 5,
    "default_year": 2023,
}

# ---------------------------------------------------------------------------
# Top 5 区域排序契约
# ---------------------------------------------------------------------------
RANKING = {
    "suitability_weight": 0.7,
    "phenology_weight": 0.3,
    "min_data_coverage": 0.8,  # 低于此比例不参与排名
}

# ---------------------------------------------------------------------------
# 降级模式
# ---------------------------------------------------------------------------
IMAGE_SERVICE_ENABLED = False   # 首周 PoC 通过后改为 True
THREE_D_ENABLED = True          # ✓ 三维功能已启用（Week 10-11完成）
AI_REALTIME_ENABLED = True      # 实时推理可用
AI_PRECOMPUTED_AVAILABLE = True # 预计算结果兜底
