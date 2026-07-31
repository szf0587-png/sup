"""天眼寻珍·苍穹 — FastAPI 主入口（v2.0）

渐进适配策略:
- Phase 0: 独立可启动，挂载系统状态 + iServer 检查
- Phase 1: 金标准 CRUD、物候匹配、GEE 状态 — 已迁入
- Phase 2: iServer 数据服务、空间分析、UDBX 发布
- Phase 3: 加固 + 基础三维
- Phase 4: 多用户系统、认证授权 — 已集成
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server.config import (
    FRONTEND_DIR, FASTAPI_HOST, FASTAPI_PORT,
    CASE_STUDY, IMAGE_SERVICE_ENABLED, THREE_D_ENABLED,
    AI_REALTIME_ENABLED, AI_PRECOMPUTED_AVAILABLE,
    GEE_PROJECT_ID,
)

# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------
app = FastAPI(title="天眼寻珍·苍穹")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ================================
# 启动事件 — 数据库初始化
# ================================
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    from server.database import init_db
    print("[startup] 正在初始化数据库...")
    init_db()
    print("[startup] 数据库初始化完成")

# ================================
# Phase 4 — 认证系统（多用户）
# ================================
from server.api.auth import router as auth_router
app.include_router(auth_router)

# ================================
# Phase 4 — 数据集管理（多用户）
# ================================
from server.api.datasets import router as datasets_router
app.include_router(datasets_router)

# ================================
# Phase 4 — 项目管理（多用户）
# ================================
from server.api.projects import router as projects_router
app.include_router(projects_router)

# ================================
# Phase 1 — 金标准 CRUD（已迁移）
# ================================
from server.api.standards import router as standards_router
app.include_router(standards_router)

# ================================
# Phase 1 — 物候匹配（已迁移）
# ================================
from server.api.phenology import router as phenology_router
app.include_router(phenology_router)

# ================================
# Phase 0 — GEE 状态
# ================================
@app.get("/api/gee-status")
def gee_status():
    """检查 Earth Engine 是否可用"""
    try:
        import ee
        ee.data.getAssetRoots()
        return {"gee_available": True, "message": "Earth Engine 可用", "project_id": GEE_PROJECT_ID}
    except Exception as e:
        return {"gee_available": False, "message": str(e)[:200], "project_id": GEE_PROJECT_ID}

# ================================
# Phase 0 — 系统状态
# ================================
@app.get("/api/system/status")
def system_status():
    from server.integrations.iserver_client import check_iserver
    iserver_ok = check_iserver()
    return {
        "status": "ok", "version": "2.0.0",
        "case_study": CASE_STUDY,
        "services": {
            "iserver": "online" if iserver_ok else "offline",
        },
        "features": {
            "image_service": IMAGE_SERVICE_ENABLED,
            "three_d": THREE_D_ENABLED,
            "ai_realtime": AI_REALTIME_ENABLED,
            "ai_precomputed": AI_PRECOMPUTED_AVAILABLE,
        },
    }

# ================================
# Phase 1 — 区域筛选（已迁移）
# ================================
from server.api.screening import router as screening_router
app.include_router(screening_router)

# ================================
# Phase 2 — 地块精评（已迁移）
# ================================
from server.api.parcels import router as parcels_router
app.include_router(parcels_router)

# ================================
# Phase 2 — 报告（已迁移）
# ================================
from server.api.reports import router as reports_router
app.include_router(reports_router)

# ================================
# Phase 3 — 土地资源评估
# ================================
from server.api.land_assessment import router as land_assessment_router
app.include_router(land_assessment_router)

# ================================
# Week 1-2 — 空间分析API（iServer深度集成）
# ================================
from server.api.spatial_analysis import router as spatial_analysis_router
app.include_router(spatial_analysis_router)

# ================================
# Week 3 — 地图服务API（iServer地图服务集成）
# ================================
from server.api.map_services import router as map_services_router
app.include_router(map_services_router)

# ================================
# Week 4 — 数据编辑API（要素增删改）
# ================================
from server.api.data_editing import router as data_editing_router
app.include_router(data_editing_router)

# ================================
# Week 9 — 数据管理API（属性表、导入导出）
# ================================
from server.api.data_management import router as data_management_router
app.include_router(data_management_router)

# ================================
# Week 10-11 — 三维服务API（场景、地形、模型）
# ================================
from server.api.scene_3d import router as scene_3d_router
app.include_router(scene_3d_router)

# ================================
# Phase 2 — 状态占位
# ================================

@app.get("/api/facilities/status")
def facilities_status():
    return {"ready": True, "message": "模拟模式可用", "precomputed": AI_PRECOMPUTED_AVAILABLE}

# ---------------------------------------------------------------------------
# 静态文件
# ---------------------------------------------------------------------------
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host=FASTAPI_HOST, port=FASTAPI_PORT, reload=False)
