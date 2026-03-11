from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Literal

from app.db.base import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.workflow import Workflow, WorkflowExecution, NodeExecution, ExecutionStatus
from app.models.component import Component
from app.services.monitor_service import MonitorService

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    period: Optional[str] = Query(None, description="统计周期: today/week/month"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取Dashboard统计数据"""
    # 基础统计
    basic_stats = MonitorService.get_basic_stats(db)
    
    # 时间段统计
    period_stats = MonitorService.get_execution_stats_by_period(db)
    
    # 最近执行
    recent_executions = db.query(WorkflowExecution).order_by(
        WorkflowExecution.created_at.desc()
    ).limit(5).all()
    
    recent_list = []
    from datetime import datetime
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
            "id": str(exec.id),
            "name": workflow_name,
            "status": exec.status,
            "time": time_str
        })
    
    # 根据period参数返回不同的统计数据
    data = {
        "workflow_count": basic_stats["workflow_count"],
        "component_count": basic_stats["component_count"],
        "today_executions": period_stats["today"],
        "this_week_executions": period_stats["this_week"],
        "this_month_executions": period_stats["this_month"],
        "success_rate": basic_stats["success_rate"],
        "status_breakdown": period_stats["status_breakdown"],
        "avg_duration_ms": period_stats["avg_duration_ms"],
        "today_avg_duration_ms": period_stats["today_avg_duration_ms"],
        "recent_executions": recent_list
    }
    
    return {
        "success": True,
        "data": data
    }


@router.get("/executions/realtime")
def get_realtime_executions(
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取实时执行状态
    
    返回正在执行和待执行的workflow列表，包含进度信息
    """
    data = MonitorService.get_realtime_executions(db, limit=limit)
    
    return {
        "success": True,
        "data": data
    }


@router.get("/executions/trend")
def get_execution_trend(
    period: Literal["hour", "day", "week"] = Query("day", description="时间粒度: hour/day/week"),
    days: int = Query(7, ge=1, le=30, description="查询天数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取执行趋势
    
    按小时/天/周统计执行数据，包含成功/失败趋势
    """
    data = MonitorService.get_execution_trend(db, period=period, days=days)
    
    return {
        "success": True,
        "data": data
    }


@router.get("/nodes/stats")
def get_node_execution_stats(
    limit: int = Query(20, ge=1, le=50, description="返回节点类型数量"),
    include_slow_nodes: bool = Query(True, description="是否包含慢节点统计"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取节点执行统计
    
    各类型节点执行次数、平均耗时、失败率排行
    """
    data = MonitorService.get_node_execution_stats(db, limit=limit)
    
    # 添加慢节点统计
    if include_slow_nodes:
        data["slow_nodes"] = MonitorService.get_slow_nodes(db, limit=10)
    
    return {
        "success": True,
        "data": data
    }


@router.get("/workflows/popular")
def get_popular_workflows(
    limit: int = Query(10, ge=1, le=20, description="返回工作流数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取最活跃工作流
    
    执行次数最多的工作流和最近执行的工作流
    """
    data = MonitorService.get_popular_workflows(db, limit=limit)
    
    return {
        "success": True,
        "data": data
    }


@router.get("/alerts")
def get_dashboard_alerts(
    failed_limit: int = Query(10, ge=1, le=50, description="失败执行显示数量"),
    timeout_threshold: int = Query(300, ge=60, le=3600, description="超时阈值(秒)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取异常告警
    
    包含失败的执行、超时的工作流、错误率过高的工作流
    """
    data = MonitorService.get_alerts(
        db,
        failed_limit=failed_limit,
        timeout_threshold=timeout_threshold
    )
    
    return {
        "success": True,
        "data": data
    }


@router.get("/health")
def get_system_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取系统健康状态
    
    返回系统健康度评分和状态
    """
    data = MonitorService.get_system_health(db)
    
    return {
        "success": True,
        "data": data
    }


@router.get("/overview")
def get_full_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取完整Dashboard概览
    
    聚合所有监控数据的综合视图
    """
    data = MonitorService.get_full_dashboard_data(db)
    
    return {
        "success": True,
        "data": data
    }


@router.post("/cache/clear")
def clear_monitor_cache(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    清除监控数据缓存
    
    用于强制刷新监控数据
    """
    MonitorService.clear_cache()
    
    return {
        "success": True,
        "message": "监控数据缓存已清除"
    }
