from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.base import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.workflow import Workflow, WorkflowExecution
from app.models.component import Component

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取Dashboard统计数据"""
    # 工作流统计
    workflow_count = db.query(func.count(Workflow.id)).scalar() or 0
    
    # 组件统计
    component_count = db.query(func.count(Component.id)).scalar() or 0
    
    # 今日执行统计
    from datetime import datetime, timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_executions = db.query(func.count(WorkflowExecution.id)).filter(
        WorkflowExecution.created_at >= today
    ).scalar() or 0
    
    # 执行成功率
    total_executions = db.query(func.count(WorkflowExecution.id)).scalar() or 0
    success_executions = db.query(func.count(WorkflowExecution.id)).filter(
        WorkflowExecution.status == "success"
    ).scalar() or 0
    
    success_rate = round((success_executions / total_executions * 100), 1) if total_executions > 0 else 0
    
    # 最近执行
    recent_executions = db.query(WorkflowExecution).order_by(
        WorkflowExecution.created_at.desc()
    ).limit(5).all()
    
    recent_list = []
    for exec in recent_executions:
        workflow = db.query(Workflow).filter(Workflow.id == exec.workflow_id).first()
        workflow_name = workflow.name if workflow else "未知工作流"
        
        # 计算时间差
        time_diff = datetime.utcnow() - exec.created_at
        if time_diff.days > 0:
            time_str = f"{time_diff.days}天前"
        elif time_diff.seconds // 3600 > 0:
            time_str = f"{time_diff.seconds // 3600}小时前"
        elif time_diff.seconds // 60 > 0:
            time_str = f"{time_diff.seconds // 60}分钟前"
        else:
            time_str = "刚刚"
        
        recent_list.append({
            "id": exec.id,
            "name": workflow_name,
            "status": exec.status,
            "time": time_str
        })
    
    return {
        "success": True,
        "data": {
            "workflow_count": workflow_count,
            "component_count": component_count,
            "today_executions": today_executions,
            "success_rate": success_rate,
            "recent_executions": recent_list
        }
    }
