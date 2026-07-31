"""土地资源评估 API 路由"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from server.database import get_db
from server.middleware.auth import get_current_user
from server.models.project import Project
from server.models.user import User
from server.schemas.land_assessment import (
    LandAssessmentRequest,
    LandAssessmentResponse,
)
from server.services.land_assessment import (
    diagnose_land_component,
    evaluate_land_resource,
    load_land_assessment,
    list_land_assessment_capabilities,
)

router = APIRouter(prefix="/api/land-assessment", tags=["land-assessment"])


@router.get("/capabilities")
def capabilities():
    """返回当前可用的评估能力摘要。"""
    return list_land_assessment_capabilities()


@router.post("/evaluate", response_model=LandAssessmentResponse)
def evaluate(
    req: LandAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """执行土地资源评估。"""
    if req.project_id:
        project = db.query(Project).filter(Project.id == req.project_id, Project.is_deleted == False).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {req.project_id} 不存在",
            )
        if project.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权使用此项目",
            )

    try:
        return evaluate_land_resource(
            boundary=req.boundary,
            target_use=req.target_use,
            project_id=req.project_id,
            user_id=current_user.id,
            buffer_distance_m=req.buffer_distance_m,
            constraint_datasets=req.constraint_datasets,
            accessibility_layers=[layer.model_dump() for layer in req.accessibility_layers or []],
            scene_name=req.scene_name,
            use_3d=req.use_3d,
            weights=req.weights,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/diagnostics/{component}")
def diagnose(
    component: str,
    req: LandAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run one reusable land-analysis component without persisting an assessment run."""
    supported_components = {"buffer", "water_constraint", "road_access", "admin_context", "land_summary"}
    if component not in supported_components:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="不支持的专题诊断类型")

    if req.project_id:
        project = db.query(Project).filter(Project.id == req.project_id, Project.is_deleted == False).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"项目 {req.project_id} 不存在")
        if project.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权使用此项目")

    try:
        return diagnose_land_component(
            component=component,
            boundary=req.boundary,
            target_use=req.target_use,
            buffer_distance_m=req.buffer_distance_m,
            constraint_datasets=req.constraint_datasets,
            accessibility_layers=[layer.model_dump() for layer in req.accessibility_layers or []],
            scene_name=req.scene_name,
            use_3d=req.use_3d,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/runs/{run_id}", response_model=LandAssessmentResponse)
def get_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
):
    """读取已保存的土地资源评估快照。"""
    result = load_land_assessment(run_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"评估记录 {run_id} 不存在",
        )
    if result.get("user_id") and result["user_id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此评估结果",
        )
    return result


@router.get("/runs/{run_id}/report", response_class=HTMLResponse)
def get_report(
    run_id: str,
    current_user: User = Depends(get_current_user),
):
    result = load_land_assessment(run_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"评估记录 {run_id} 不存在",
        )
    if result.get("user_id") and result["user_id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此评估报告",
        )
    report_path = result.get("report_path")
    if not report_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告文件不存在",
        )
    from pathlib import Path

    path = Path(report_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告文件不存在",
        )
    return path.read_text(encoding="utf-8")
