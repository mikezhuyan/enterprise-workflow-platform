"""
审批任务API
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.security import get_current_user
from app.services.workflow_service import ApprovalTaskService
from app.schemas.workflow import (
    ApprovalTaskResponse, ApprovalTaskListResponse,
    ApprovalActionRequest, ApprovalTransferRequest, ApprovalActionResponse
)
from app.schemas.user import PaginatedResponse
from app.models.user import User

router = APIRouter()


def get_user_role_ids(user: User) -> List[UUID]:
    """获取用户的角色ID列表"""
    return [role.id for role in user.roles] if hasattr(user, 'roles') and user.roles else []


@router.get("/pending", response_model=PaginatedResponse)
def list_pending_approvals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的待审批列表"""
    skip = (page - 1) * page_size
    
    # 获取用户的角色ID列表
    role_ids = get_user_role_ids(current_user)
    
    # 获取部门ID
    department_id = current_user.department_id if hasattr(current_user, 'department_id') else None
    
    tasks, total = ApprovalTaskService.list_pending_tasks(
        db,
        user_id=current_user.id,
        role_ids=role_ids if role_ids else None,
        department_id=department_id,
        skip=skip,
        limit=page_size
    )
    
    # 转换为响应模型
    task_list = [ApprovalTaskListResponse.model_validate(t).model_dump() for t in tasks]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "data": task_list
    }


@router.get("/my", response_model=PaginatedResponse)
def list_my_approvals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户已审批的列表"""
    skip = (page - 1) * page_size
    
    tasks, total = ApprovalTaskService.list_user_tasks(
        db,
        user_id=current_user.id,
        status=status,
        skip=skip,
        limit=page_size
    )
    
    # 转换为响应模型
    task_list = [ApprovalTaskListResponse.model_validate(t).model_dump() for t in tasks]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "data": task_list
    }


@router.get("/{approval_id}", response_model=ApprovalTaskResponse)
def get_approval_detail(
    approval_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取审批详情"""
    task = ApprovalTaskService.get_task_by_id(db, approval_id)
    if not task:
        raise HTTPException(status_code=404, detail="审批任务不存在")
    
    return task


@router.post("/{approval_id}/approve", response_model=ApprovalActionResponse)
def approve_task(
    approval_id: UUID,
    action_data: ApprovalActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """审批通过"""
    # 检查权限
    role_ids = get_user_role_ids(current_user)
    department_id = current_user.department_id if hasattr(current_user, 'department_id') else None
    
    if not ApprovalTaskService.check_user_can_approve(
        db, approval_id, current_user.id, role_ids, department_id
    ):
        raise HTTPException(status_code=403, detail="无权审批此任务")
    
    try:
        task = ApprovalTaskService.approve_task(
            db,
            task_id=approval_id,
            user_id=current_user.id,
            comment=action_data.comment
        )
        
        return ApprovalActionResponse(
            success=True,
            message="审批已通过",
            task_id=task.id,
            status=task.status,
            completed_at=task.completed_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{approval_id}/reject", response_model=ApprovalActionResponse)
def reject_task(
    approval_id: UUID,
    action_data: ApprovalActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """审批拒绝"""
    # 检查权限
    role_ids = get_user_role_ids(current_user)
    department_id = current_user.department_id if hasattr(current_user, 'department_id') else None
    
    if not ApprovalTaskService.check_user_can_approve(
        db, approval_id, current_user.id, role_ids, department_id
    ):
        raise HTTPException(status_code=403, detail="无权审批此任务")
    
    try:
        task = ApprovalTaskService.reject_task(
            db,
            task_id=approval_id,
            user_id=current_user.id,
            comment=action_data.comment
        )
        
        return ApprovalActionResponse(
            success=True,
            message="审批已拒绝",
            task_id=task.id,
            status=task.status,
            completed_at=task.completed_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{approval_id}/transfer", response_model=ApprovalActionResponse)
def transfer_task(
    approval_id: UUID,
    transfer_data: ApprovalTransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """转办审批任务"""
    # 检查权限
    role_ids = get_user_role_ids(current_user)
    department_id = current_user.department_id if hasattr(current_user, 'department_id') else None
    
    if not ApprovalTaskService.check_user_can_approve(
        db, approval_id, current_user.id, role_ids, department_id
    ):
        raise HTTPException(status_code=403, detail="无权转办此任务")
    
    try:
        task = ApprovalTaskService.transfer_task(
            db,
            task_id=approval_id,
            user_id=current_user.id,
            new_assignee_id=transfer_data.new_assignee_id,
            comment=transfer_data.comment
        )
        
        return ApprovalActionResponse(
            success=True,
            message="审批任务已转办",
            task_id=task.id,
            status=task.status,
            completed_at=task.transferred_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
