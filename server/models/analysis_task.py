"""分析任务模型"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Text
from server.database import Base


class AnalysisTask(Base):
    """分析任务表 - 追踪异步GIS分析任务"""
    __tablename__ = "analysis_tasks"

    id = Column(String, primary_key=True)  # UUID: task_xxx
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)

    task_type = Column(String, nullable=False, comment="任务类型: slope_analysis/ndvi/flood_risk等")
    status = Column(String, default="pending", nullable=False, comment="任务状态: pending/running/completed/failed")

    # 输入参数
    input_params = Column(JSON, nullable=True, comment="输入参数（数据集ID、分析参数等）")

    # 输出结果
    output_path = Column(String, nullable=True, comment="输出文件路径（相对路径）")
    result_metadata = Column(JSON, nullable=True, comment="结果元数据（统计信息、可视化配置等）")

    # 执行信息
    progress = Column(Integer, default=0, nullable=False, comment="执行进度 0-100")
    error_message = Column(Text, nullable=True, comment="错误信息")

    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AnalysisTask(id={self.id}, type={self.task_type}, status={self.status}, progress={self.progress}%)>"
