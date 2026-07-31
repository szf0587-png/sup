"""区域筛选 API 路由（数据库版本 - 多用户支持）"""
from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from server.database import get_db
from server.models.user import User
from server.models.golden_standard import GoldenStandard
from server.middleware.auth import get_current_user
from server.schemas.screening import ScreeningRequest, ScreeningResponse
from server.services.town_ranking import rank_towns
from server.config import SNAPSHOTS_DIR

router = APIRouter(prefix="/api/screening", tags=["screening"])


@router.post("/runs")
def start_screening(
    req: ScreeningRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    启动区域筛选任务，返回 Top N 候选乡镇

    - 从数据库读取当前用户的金标准
    - 基于金标准进行乡镇排序
    - 只能使用自己的金标准
    """
    # 验证金标准是否存在且属于当前用户
    golden_standard = db.query(GoldenStandard).filter(
        GoldenStandard.id == req.golden_standard_id,
        GoldenStandard.is_deleted == False
    ).first()

    if not golden_standard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"金标准 {req.golden_standard_id} 不存在"
        )

    # 权限检查：只能使用自己的金标准
    if golden_standard.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权使用此金标准"
        )

    # 调用乡镇排序服务
    result = rank_towns(
        golden_standard_id=req.golden_standard_id,
        top_n=req.top_n,
        county=req.county,
    )

    # 添加金标准信息到结果
    result["golden_standard_id"] = req.golden_standard_id
    result["golden_standard_name"] = golden_standard.model_name
    result["user_id"] = current_user.id

    return result


@router.get("/runs/{run_id}")
def get_screening_result(
    run_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取已完成的筛选任务结果（从快照读取）

    - 读取快照文件
    - 验证快照属于当前用户（如果快照包含 user_id）
    """
    snap = SNAPSHOTS_DIR / f"{run_id}.json"
    if not snap.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"快照 {run_id} 不存在"
        )

    with open(snap, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 如果快照包含 user_id，验证权限
    snapshot_user_id = data.get("user_id")
    if snapshot_user_id and snapshot_user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此快照"
        )

    return data
