"""
工作流服务
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.workflow import (
    Workflow, WorkflowExecution, NodeExecution, ExecutionLog,
    WorkflowCategory, WorkflowSchedule, WorkflowStatus, ExecutionStatus
)
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate


class WorkflowService:
    """工作流服务"""
    
    @staticmethod
    def get_by_id(db: Session, workflow_id: UUID) -> Optional[Workflow]:
        """根据ID获取工作流"""
        return db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    @staticmethod
    def list_workflows(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        category_id: Optional[UUID] = None,
        status: Optional[str] = None,
        tenant_id: Optional[UUID] = None
    ) -> tuple:
        """获取工作流列表"""
        query = db.query(Workflow)
        
        if tenant_id:
            query = query.filter(Workflow.tenant_id == tenant_id)
        
        if category_id:
            query = query.filter(Workflow.category_id == category_id)
        
        if status:
            query = query.filter(Workflow.status == status)
        
        if search:
            query = query.filter(
                Workflow.name.ilike(f"%{search}%") |
                Workflow.description.ilike(f"%{search}%")
            )
        
        total = query.count()
        workflows = query.order_by(Workflow.created_at.desc()).offset(skip).limit(limit).all()
        return workflows, total
    
    @staticmethod
    def create_workflow(db: Session, workflow_data: WorkflowCreate, user_id: UUID, tenant_id: Optional[UUID] = None) -> Workflow:
        """创建工作流"""
        db_workflow = Workflow(
            name=workflow_data.name,
            description=workflow_data.description,
            version="1.0.0",
            status=WorkflowStatus.DRAFT.value,
            is_template=workflow_data.is_template,
            definition=workflow_data.definition.model_dump() if workflow_data.definition else {"nodes": [], "edges": []},
            variables=[v.model_dump() for v in workflow_data.variables] if workflow_data.variables else [],
            triggers=[t.model_dump() for t in workflow_data.triggers] if workflow_data.triggers else [],
            category_id=workflow_data.category_id,
            tags=workflow_data.tags or [],
            created_by=user_id,
            tenant_id=tenant_id,
        )
        
        db.add(db_workflow)
        db.commit()
        db.refresh(db_workflow)
        return db_workflow
    
    @staticmethod
    def update_workflow(db: Session, workflow: Workflow, workflow_data: WorkflowUpdate) -> Workflow:
        """更新工作流"""
        update_data = workflow_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field in ['definition', 'variables', 'triggers'] and value is not None:
                if field == 'definition':
                    # 只有Pydantic模型才需要调用model_dump()
                    if hasattr(value, 'model_dump'):
                        value = value.model_dump()
                elif field in ['variables', 'triggers']:
                    # 处理列表中的每个元素
                    value = [v.model_dump() if hasattr(v, 'model_dump') else v for v in value]
            setattr(workflow, field, value)
        
        workflow.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)
        return workflow
    
    @staticmethod
    def delete_workflow(db: Session, workflow: Workflow) -> None:
        """删除工作流"""
        db.delete(workflow)
        db.commit()
    
    @staticmethod
    def publish_workflow(db: Session, workflow: Workflow, version: Optional[str] = None) -> Workflow:
        """发布工作流"""
        if version:
            workflow.version = version
        else:
            # 自动递增版本号
            parts = workflow.version.split('.')
            parts[-1] = str(int(parts[-1]) + 1)
            workflow.version = '.'.join(parts)
        
        workflow.status = WorkflowStatus.PUBLISHED.value
        workflow.published_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)
        return workflow
    
    @staticmethod
    def get_execution_by_id(db: Session, execution_id: UUID) -> Optional[WorkflowExecution]:
        """根据ID获取执行记录"""
        return db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    
    @staticmethod
    def list_executions(
        db: Session,
        workflow_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> tuple:
        """获取执行记录列表"""
        query = db.query(WorkflowExecution).filter(WorkflowExecution.workflow_id == workflow_id)
        
        if status:
            query = query.filter(WorkflowExecution.status == status)
        
        total = query.count()
        executions = query.order_by(WorkflowExecution.created_at.desc()).offset(skip).limit(limit).all()
        return executions, total
    
    @staticmethod
    def create_execution(db: Session, workflow_id: UUID, input_data: Dict, triggered_by: Optional[UUID] = None) -> WorkflowExecution:
        """创建执行记录"""
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status=ExecutionStatus.PENDING.value,
            input_data=input_data,
            triggered_by=triggered_by,
            trigger_type="manual",
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution


class WorkflowCategoryService:
    """工作流分类服务"""
    
    @staticmethod
    def get_categories(db: Session) -> List[WorkflowCategory]:
        """获取所有分类"""
        return db.query(WorkflowCategory).order_by(WorkflowCategory.sort_order).all()
    
    @staticmethod
    def create_category(db: Session, name: str, **kwargs) -> WorkflowCategory:
        """创建分类"""
        category = WorkflowCategory(name=name, **kwargs)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
