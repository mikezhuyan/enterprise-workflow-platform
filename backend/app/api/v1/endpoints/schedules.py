from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.security import get_current_user
from app.services.scheduler_service import WorkflowScheduleService
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import (
    WorkflowScheduleCreate, WorkflowScheduleUpdate, WorkflowScheduleResponse
)
from app.schemas.user import PaginatedResponse
from app.models.user import User
from app.models.workflow import WorkflowSchedule

# 用于 /api/v1/workflows 前缀的路由（工作流下的定时任务）
router = APIRouter()

# 用于 /api/v1/schedules 前缀的路由（独立的定时任务操作）
schedule_router = APIRouter()


def _to_response(schedule: WorkflowSchedule) -> WorkflowScheduleResponse:
    """将模型转换为响应Schema"""
    return WorkflowScheduleResponse(
        id=schedule.id,
        workflow_id=schedule.workflow_id,
        cron_expression=schedule.cron_expression,
        timezone=schedule.timezone,
        input_data=schedule.input_data or {},
        is_active=schedule.is_active,
        next_run_at=schedule.next_run_at,
        last_run_at=schedule.last_run_at,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at
    )


@router.get("/{workflow_id}/schedules", response_model=PaginatedResponse)
def list_workflow_schedules(
    workflow_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取工作流的定时任务列表"""
    # 检查工作流是否存在
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    skip = (page - 1) * page_size
    schedules, total = WorkflowScheduleService.list_by_workflow(
        db, workflow_id, skip=skip, limit=page_size
    )
    
    # 转换为响应模型
    schedule_list = [_to_response(s).model_dump() for s in schedules]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "data": schedule_list
    }


@router.post("/{workflow_id}/schedules", response_model=WorkflowScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    workflow_id: UUID,
    schedule_data: WorkflowScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建工作流定时任务"""
    # 检查工作流是否存在
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限
    if workflow.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权为此工作流创建定时任务")
    
    # 验证cron表达式格式（5部分：分 时 日 月 周）
    cron_parts = schedule_data.cron_expression.split()
    if len(cron_parts) != 5:
        raise HTTPException(
            status_code=400, 
            detail="无效的cron表达式，格式应为: 分 时 日 月 周 (如: '0 9 * * 1')"
        )
    
    try:
        schedule = WorkflowScheduleService.create_schedule(
            db, workflow_id, schedule_data
        )
        return _to_response(schedule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@schedule_router.get("/{schedule_id}", response_model=WorkflowScheduleResponse)
def get_schedule(
    schedule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取定时任务详情"""
    schedule = WorkflowScheduleService.get_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="定时任务不存在")
    
    return _to_response(schedule)


@schedule_router.put("/{schedule_id}", response_model=WorkflowScheduleResponse)
def update_schedule(
    schedule_id: UUID,
    schedule_data: WorkflowScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新定时任务"""
    schedule = WorkflowScheduleService.get_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="定时任务不存在")
    
    # 获取工作流以检查权限
    workflow = WorkflowService.get_by_id(db, schedule.workflow_id)
    if workflow.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权修改此定时任务")
    
    # 验证cron表达式格式（如果提供了）
    if schedule_data.cron_expression:
        cron_parts = schedule_data.cron_expression.split()
        if len(cron_parts) != 5:
            raise HTTPException(
                status_code=400, 
                detail="无效的cron表达式，格式应为: 分 时 日 月 周 (如: '0 9 * * 1')"
            )
    
    try:
        updated_schedule = WorkflowScheduleService.update_schedule(
            db, schedule, schedule_data
        )
        return _to_response(updated_schedule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@schedule_router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除定时任务"""
    schedule = WorkflowScheduleService.get_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="定时任务不存在")
    
    # 获取工作流以检查权限
    workflow = WorkflowService.get_by_id(db, schedule.workflow_id)
    if workflow.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权删除此定时任务")
    
    WorkflowScheduleService.delete_schedule(db, schedule)
    return None


@schedule_router.post("/{schedule_id}/pause", response_model=WorkflowScheduleResponse)
def pause_schedule(
    schedule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """暂停定时任务"""
    schedule = WorkflowScheduleService.get_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="定时任务不存在")
    
    # 获取工作流以检查权限
    workflow = WorkflowService.get_by_id(db, schedule.workflow_id)
    if workflow.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权暂停此定时任务")
    
    if not schedule.is_active:
        raise HTTPException(status_code=400, detail="定时任务已经是暂停状态")
    
    paused_schedule = WorkflowScheduleService.pause_schedule(db, schedule)
    return _to_response(paused_schedule)


@schedule_router.post("/{schedule_id}/resume", response_model=WorkflowScheduleResponse)
def resume_schedule(
    schedule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """恢复定时任务"""
    schedule = WorkflowScheduleService.get_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="定时任务不存在")
    
    # 获取工作流以检查权限
    workflow = WorkflowService.get_by_id(db, schedule.workflow_id)
    if workflow.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权恢复此定时任务")
    
    if schedule.is_active:
        raise HTTPException(status_code=400, detail="定时任务已经是激活状态")
    
    resumed_schedule = WorkflowScheduleService.resume_schedule(db, schedule)
    return _to_response(resumed_schedule)
