"""地块精评 API 路由（数据库版本 - 多用户支持）"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from server.database import get_db
from server.models.user import User
from server.models.golden_standard import GoldenStandard
from server.middleware.auth import get_current_user
from server.services.parcel_evaluation import evaluate_parcel

router = APIRouter(prefix="/api/parcels", tags=["parcels"])


class ParcelEvalRequest(BaseModel):
    town_code: str
    parcel_geojson: dict
    golden_standard_id: str


@router.post("/evaluate")
def start_evaluation(
    req: ParcelEvalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    对指定地块执行综合评价

    - 验证金标准是否存在且属于当前用户
    - 调用地块评价服务
    - 返回评价结果
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

    # 执行地块评价
    try:
        result = evaluate_parcel(
            town_code=req.town_code,
            parcel_geojson=req.parcel_geojson,
            golden_standard_id=req.golden_standard_id,
        )

        # 添加用户信息到结果
        result["user_id"] = current_user.id
        result["golden_standard_name"] = golden_standard.model_name

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"地块评价失败: {str(e)}"
        )
