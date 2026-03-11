from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.security import get_current_user
from app.services.workflow_service import WorkflowService, WorkflowCategoryService
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowListResponse,
    WorkflowExecuteRequest, WorkflowExecutionResponse, ExecutionDetailResponse,
    WorkflowCategoryCreate, WorkflowCategoryResponse, WorkflowStatsResponse,
    WorkflowVersionCreate, WorkflowVersionResponse, WorkflowVersionListResponse,
    WorkflowRollbackRequest, WorkflowRollbackResponse,
    WorkflowVersionCompareRequest, WorkflowVersionCompareResponse,
)
from app.schemas.user import PaginatedResponse
from app.models.user import User
from app.models.workflow import ExecutionStatus, NodeExecution

from typing import List, Any

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def list_workflows(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category_id: Optional[UUID] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取工作流列表"""
    skip = (page - 1) * page_size
    workflows, total = WorkflowService.list_workflows(
        db,
        skip=skip,
        limit=page_size,
        search=search,
        category_id=category_id,
        status=status,
        tenant_id=current_user.tenant_id
    )
    
    # 将SQLAlchemy对象转换为Pydantic模型
    workflow_list = [WorkflowListResponse.model_validate(w).model_dump() for w in workflows]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "data": workflow_list
    }


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建工作流"""
    try:
        workflow = WorkflowService.create_workflow(
            db, workflow_data, current_user.id, current_user.tenant_id
        )
        return workflow
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取工作流详情"""
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(
    workflow_id: UUID,
    workflow_data: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新工作流"""
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限
    if workflow.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权修改此工作流")
    
    return WorkflowService.update_workflow(db, workflow, workflow_data)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除工作流"""
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限
    if workflow.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权删除此工作流")
    
    WorkflowService.delete_workflow(db, workflow)
    return None


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: UUID,
    execute_data: WorkflowExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行工作流"""
    from app.workflow.engine import WorkflowEngine
    
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 创建工作流引擎并执行
    engine = WorkflowEngine()
    
    # 创建执行记录
    execution = WorkflowService.create_execution(
        db, workflow_id, execute_data.input_data, current_user.id
    )
    
    # 异步执行工作流
    if execute_data.synchronous:
        # 同步执行
        execution.status = ExecutionStatus.RUNNING.value
        execution.started_at = datetime.utcnow()
        db.commit()
        
        result = await engine.execute_workflow(
            workflow.definition,
            execute_data.input_data,
            str(execution.id)
        )
        
        # 更新执行记录
        execution.status = ExecutionStatus.SUCCESS.value if result.get("status") == "success" else ExecutionStatus.FAILED.value
        execution.output_data = result
        execution.completed_at = datetime.utcnow()
        
        # 计算总耗时
        if execution.started_at and execution.completed_at:
            execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
        
        db.commit()
        
        # 创建节点执行记录
        node_results = result.get("results", [])
        workflow_nodes = {n["id"]: n for n in workflow.definition.get("nodes", [])}
        
        for node_result in node_results:
            node_id = node_result.get("node_id")
            node_def = workflow_nodes.get(node_id, {})
            node_data = node_def.get("data", {})
            
            node_execution = NodeExecution(
                execution_id=execution.id,
                node_id=node_id,
                node_type=node_def.get("type", "unknown"),
                node_name=node_data.get("label") or node_data.get("name") or node_id,
                status="success" if node_result.get("status") == "success" else "failed",
                input_data={},
                output_data=node_result.get("output"),
                error_message=node_result.get("error"),
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                duration_ms=node_result.get("duration_ms", 0),
            )
            db.add(node_execution)
        
        db.commit()
        db.refresh(execution)
        
        return execution
    else:
        # 异步执行 - 启动后台任务
        execution.status = ExecutionStatus.RUNNING.value
        execution.started_at = datetime.utcnow()
        db.commit()
        db.refresh(execution)
        
        return execution


@router.post("/{workflow_id}/publish")
def publish_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布工作流"""
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限
    if workflow.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权发布此工作流")
    
    return WorkflowService.publish_workflow(db, workflow)


# ============ 执行记录 ============

@router.get("/{workflow_id}/executions", response_model=PaginatedResponse)
def list_executions(
    workflow_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取执行记录列表"""
    skip = (page - 1) * page_size
    executions, total = WorkflowService.list_executions(
        db, workflow_id, skip=skip, limit=page_size, status=status
    )
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "data": executions
    }


@router.get("/executions/{execution_id}", response_model=ExecutionDetailResponse)
def get_execution(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取执行详情"""
    execution = WorkflowService.get_execution_by_id(db, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return execution


@router.post("/executions/{execution_id}/cancel")
def cancel_execution(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消执行"""
    from app.models.workflow import ExecutionStatus
    
    execution = WorkflowService.get_execution_by_id(db, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    
    if execution.status == ExecutionStatus.RUNNING.value:
        execution.status = ExecutionStatus.CANCELLED.value
        db.commit()
    
    return {"message": "执行已取消"}


# ============ 分类管理 ============

@router.get("/categories/tree")
def get_category_tree(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取工作流分类树"""
    return WorkflowCategoryService.get_categories(db)


@router.post("/categories", response_model=WorkflowCategoryResponse)
def create_category(
    category_data: WorkflowCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建工作流分类"""
    category = WorkflowCategoryService.create_category(
        db,
        name=category_data.name,
        description=category_data.description,
        icon=category_data.icon,
        color=category_data.color,
        sort_order=category_data.sort_order or 0
    )
    return category


# ============ 统计 ============

@router.get("/stats/overview", response_model=WorkflowStatsResponse)
def get_workflow_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取工作流统计"""
    from sqlalchemy import func
    from app.models.workflow import Workflow, WorkflowExecution
    
    total_workflows = db.query(Workflow).count()
    active_workflows = db.query(Workflow).filter(Workflow.status == "published").count()
    total_executions = db.query(WorkflowExecution).count()
    
    # 计算成功率
    success_count = db.query(WorkflowExecution).filter(WorkflowExecution.status == "success").count()
    success_rate = (success_count / total_executions * 100) if total_executions > 0 else 0
    
    # 计算平均执行时间
    avg_duration = db.query(func.avg(WorkflowExecution.duration_ms)).scalar() or 0
    
    return {
        "total_workflows": total_workflows,
        "active_workflows": active_workflows,
        "total_executions": total_executions,
        "success_rate": round(success_rate, 1),
        "avg_duration_ms": int(avg_duration),
        "executions_today": 0,
        "executions_this_week": 0,
        "executions_this_month": 0
    }


# ============ 版本控制 ============

@router.post("/{workflow_id}/versions", response_model=WorkflowVersionResponse, status_code=status.HTTP_201_CREATED)
def create_workflow_version(
    workflow_id: UUID,
    version_data: WorkflowVersionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建工作流新版本"""
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限
    if workflow.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权为此工作流创建版本")
    
    # 创建新版本
    new_version = WorkflowService.create_version(
        db,
        workflow,
        version_type=version_data.version_type,
        comment=version_data.comment,
        user_id=current_user.id
    )
    
    # 提取版本说明
    definition = new_version.definition or {}
    comment = definition.get("_version_comment") if isinstance(definition, dict) else None
    
    return WorkflowVersionResponse(
        id=new_version.id,
        name=new_version.name,
        version=new_version.version,
        status=new_version.status,
        description=new_version.description,
        created_by=new_version.created_by,
        created_at=new_version.created_at,
        parent_id=new_version.parent_id,
        comment=comment
    )


@router.get("/{workflow_id}/versions", response_model=WorkflowVersionListResponse)
def list_workflow_versions(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取工作流的所有版本"""
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 获取所有版本
    versions = WorkflowService.get_versions(db, workflow_id, include_parent=True)
    
    # 转换为响应格式
    version_list = []
    for v in versions:
        definition = v.definition or {}
        comment = definition.get("_version_comment") if isinstance(definition, dict) else None
        version_list.append(WorkflowVersionResponse(
            id=v.id,
            name=v.name,
            version=v.version,
            status=v.status,
            description=v.description,
            created_by=v.created_by,
            created_at=v.created_at,
            parent_id=v.parent_id,
            comment=comment
        ))
    
    return WorkflowVersionListResponse(
        versions=version_list,
        total=len(version_list)
    )


@router.get("/{workflow_id}/versions/{version}", response_model=WorkflowResponse)
def get_workflow_version(
    workflow_id: UUID,
    version: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定版本的工作流"""
    target_version = WorkflowService.get_version_by_number(db, workflow_id, version)
    if not target_version:
        raise HTTPException(status_code=404, detail="指定版本不存在")
    
    return target_version


@router.post("/{workflow_id}/versions/{version}/rollback", response_model=WorkflowRollbackResponse)
def rollback_to_version(
    workflow_id: UUID,
    version: str,
    rollback_data: WorkflowRollbackRequest = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """回滚到指定版本"""
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限
    if workflow.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权回滚此工作流")
    
    # 检查目标版本是否存在
    target = WorkflowService.get_version_by_number(db, workflow_id, version)
    if not target:
        raise HTTPException(status_code=404, detail="目标版本不存在")
    
    # 执行回滚
    comment = rollback_data.comment if rollback_data else None
    new_workflow = WorkflowService.rollback_to_version(
        db,
        workflow_id,
        version,
        user_id=current_user.id
    )
    
    if not new_workflow:
        raise HTTPException(status_code=500, detail="回滚失败")
    
    return WorkflowRollbackResponse(
        message=f"成功回滚到版本 {version}",
        new_version=new_workflow.version,
        workflow_id=new_workflow.id
    )


@router.get("/{workflow_id}/versions/compare", response_model=WorkflowVersionCompareResponse)
def compare_workflow_versions(
    workflow_id: UUID,
    version1: str = Query(..., description="基准版本号"),
    version2: str = Query(..., description="对比版本号"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """比较两个版本的差异"""
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 比较版本
    result = WorkflowService.compare_versions(db, workflow_id, version1, version2)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return WorkflowVersionCompareResponse(
        version1=result["version1"],
        version2=result["version2"],
        workflow_id=result["workflow_id"],
        changes=result["changes"],
        summary=result["summary"],
        diff_text=result.get("diff_text")
    )
