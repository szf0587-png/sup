"""报告 API 路由（数据库版本 - 多用户支持）"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from server.database import get_db
from server.models.user import User
from server.middleware.auth import get_current_user
from server.config import SNAPSHOTS_DIR, DATA_DIR
from server.services.report_builder import build_report, export_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportRequest(BaseModel):
    screening_run_id: str
    parcel_run_id: Optional[str] = None


@router.post("/generate")
def generate_report(
    req: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成决策报告

    - 验证筛选快照是否存在
    - 验证快照属于当前用户
    - 生成 HTML 报告
    """
    # 加载筛选结果快照
    scr_snap = SNAPSHOTS_DIR / f"{req.screening_run_id}.json"
    if not scr_snap.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"筛选快照 {req.screening_run_id} 不存在"
        )

    with open(scr_snap, "r", encoding="utf-8") as f:
        screening = json.load(f)

    # 验证快照属于当前用户
    snapshot_user_id = screening.get("user_id")
    if snapshot_user_id and snapshot_user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此筛选快照"
        )

    # 加载地块结果（如果有）
    parcel = None
    if req.parcel_run_id:
        par_snap = SNAPSHOTS_DIR / f"{req.parcel_run_id}.json"
        if par_snap.exists():
            with open(par_snap, "r", encoding="utf-8") as f:
                parcel = json.load(f)

            # 验证地块快照属于当前用户
            parcel_user_id = parcel.get("user_id")
            if parcel_user_id and parcel_user_id != current_user.id and current_user.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此地块快照"
                )

    # 生成报告
    try:
        run_id = req.screening_run_id
        path = export_report(run_id, screening, parcel)
        return {
            "status": "ok",
            "run_id": run_id,
            "path": str(path),
            "user_id": current_user.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报告生成失败: {str(e)}"
        )


@router.get("/{run_id}", response_class=HTMLResponse)
def view_report(
    run_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    查看已生成的报告

    - 验证报告是否存在
    - 验证报告属于当前用户（通过快照验证）
    """
    # 检查报告文件是否存在
    path = DATA_DIR / "outputs" / f"report_{run_id}.html"
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告未生成"
        )

    # 验证报告属于当前用户（通过对应的快照）
    scr_snap = SNAPSHOTS_DIR / f"{run_id}.json"
    if scr_snap.exists():
        with open(scr_snap, "r", encoding="utf-8") as f:
            screening = json.load(f)

        snapshot_user_id = screening.get("user_id")
        if snapshot_user_id and snapshot_user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此报告"
            )

    return path.read_text(encoding="utf-8")
