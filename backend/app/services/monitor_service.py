"""
监控服务 - 提供Dashboard统计数据和实时监控功能
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_, case, cast, Float
from functools import lru_cache
import time

from app.models.workflow import (
    Workflow, WorkflowExecution, NodeExecution, ExecutionStatus
)
from app.models.component import Component


class MonitorService:
    """监控服务"""
    
    # 缓存相关配置
    _cache = {}
    _cache_ttl = {}
    CACHE_DURATION = 30  # 默认缓存30秒
    
    @classmethod
    def _get_cached(cls, key: str) -> Optional[Any]:
        """获取缓存数据"""
        if key in cls._cache and key in cls._cache_ttl:
            if time.time() < cls._cache_ttl[key]:
                return cls._cache[key]
        return None
    
    @classmethod
    def _set_cached(cls, key: str, value: Any, ttl: int = None):
        """设置缓存数据"""
        cls._cache[key] = value
        cls._cache_ttl[key] = time.time() + (ttl or cls.CACHE_DURATION)
    
    @classmethod
    def clear_cache(cls):
        """清除缓存"""
        cls._cache.clear()
        cls._cache_ttl.clear()
    
    # ==================== 基础统计 ====================
    
    @staticmethod
    def get_basic_stats(db: Session) -> Dict[str, Any]:
        """获取基础统计数据"""
        # 工作流统计
        workflow_count = db.query(func.count(Workflow.id)).scalar() or 0
        
        # 组件统计
        component_count = db.query(func.count(Component.id)).scalar() or 0
        
        # 执行统计
        total_executions = db.query(func.count(WorkflowExecution.id)).scalar() or 0
        
        # 今日执行统计
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_executions = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.created_at >= today
        ).scalar() or 0
        
        # 成功率
        success_count = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.status == ExecutionStatus.SUCCESS.value
        ).scalar() or 0
        success_rate = round((success_count / total_executions * 100), 1) if total_executions > 0 else 0
        
        return {
            "workflow_count": workflow_count,
            "component_count": component_count,
            "total_executions": total_executions,
            "today_executions": today_executions,
            "success_rate": success_rate
        }
    
    @staticmethod
    def get_execution_stats_by_period(db: Session) -> Dict[str, Any]:
        """获取各时间段执行统计"""
        now = datetime.utcnow()
        
        # 今日
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_executions = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.created_at >= today_start
        ).scalar() or 0
        
        # 本周
        week_start = today_start - timedelta(days=today_start.weekday())
        week_executions = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.created_at >= week_start
        ).scalar() or 0
        
        # 本月
        month_start = today_start.replace(day=1)
        month_executions = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.created_at >= month_start
        ).scalar() or 0
        
        # 各状态统计
        status_counts = db.query(
            WorkflowExecution.status,
            func.count(WorkflowExecution.id).label('count')
        ).group_by(WorkflowExecution.status).all()
        
        status_stats = {
            "pending": 0,
            "running": 0,
            "success": 0,
            "failed": 0,
            "cancelled": 0,
            "timeout": 0
        }
        for status, count in status_counts:
            status_stats[status] = count
        
        # 平均执行时间趋势
        avg_duration = db.query(func.avg(WorkflowExecution.duration_ms)).filter(
            WorkflowExecution.duration_ms.isnot(None),
            WorkflowExecution.completed_at.isnot(None)
        ).scalar() or 0
        
        # 今日平均执行时间
        today_avg_duration = db.query(func.avg(WorkflowExecution.duration_ms)).filter(
            WorkflowExecution.duration_ms.isnot(None),
            WorkflowExecution.created_at >= today_start
        ).scalar() or 0
        
        return {
            "today": today_executions,
            "this_week": week_executions,
            "this_month": month_executions,
            "status_breakdown": status_stats,
            "avg_duration_ms": round(avg_duration, 2),
            "today_avg_duration_ms": round(today_avg_duration, 2)
        }
    
    # ==================== 实时执行监控 ====================
    
    @staticmethod
    def get_realtime_executions(db: Session, limit: int = 50) -> Dict[str, Any]:
        """获取实时执行状态"""
        # 正在执行的数量
        running_count = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.status == ExecutionStatus.RUNNING.value
        ).scalar() or 0
        
        pending_count = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.status == ExecutionStatus.PENDING.value
        ).scalar() or 0
        
        # 正在执行的列表
        running_executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.status.in_([
                ExecutionStatus.RUNNING.value,
                ExecutionStatus.PENDING.value
            ])
        ).order_by(desc(WorkflowExecution.started_at)).limit(limit).all()
        
        executions_list = []
        for exec in running_executions:
            workflow = db.query(Workflow).filter(Workflow.id == exec.workflow_id).first()
            workflow_name = workflow.name if workflow else "未知工作流"
            
            # 获取当前执行的节点
            current_node = db.query(NodeExecution).filter(
                NodeExecution.execution_id == exec.id,
                NodeExecution.status == ExecutionStatus.RUNNING.value
            ).first()
            
            # 计算进度
            total_nodes = len(workflow.definition.get('nodes', [])) if workflow and workflow.definition else 0
            completed_nodes = db.query(func.count(NodeExecution.id)).filter(
                NodeExecution.execution_id == exec.id,
                NodeExecution.status == ExecutionStatus.SUCCESS.value
            ).scalar() or 0
            
            progress = round((completed_nodes / total_nodes * 100), 1) if total_nodes > 0 else 0
            
            executions_list.append({
                "id": str(exec.id),
                "workflow_id": str(exec.workflow_id),
                "workflow_name": workflow_name,
                "status": exec.status,
                "started_at": exec.started_at.isoformat() if exec.started_at else None,
                "current_node": current_node.node_name if current_node else None,
                "current_node_type": current_node.node_type if current_node else None,
                "progress": progress,
                "trigger_type": exec.trigger_type,
                "duration_ms": exec.duration_ms
            })
        
        return {
            "running_count": running_count,
            "pending_count": pending_count,
            "total_active": running_count + pending_count,
            "executions": executions_list
        }
    
    # ==================== 执行趋势分析 ====================
    
    @staticmethod
    def get_execution_trend(
        db: Session,
        period: str = "day",
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取执行趋势
        
        Args:
            period: 时间粒度 - hour(小时), day(天), week(周)
            days: 查询天数
        """
        now = datetime.utcnow()
        start_time = now - timedelta(days=days)
        
        if period == "hour":
            # 按小时分组
            format_str = "%Y-%m-%d %H:00"
            date_trunc = func.strftime('%Y-%m-%d %H', WorkflowExecution.created_at)
        elif period == "day":
            # 按天分组
            date_trunc = func.date(WorkflowExecution.created_at)
        else:  # week
            # 按周分组
            date_trunc = func.strftime('%Y-%W', WorkflowExecution.created_at)
        
        # 查询各时间段的执行统计
        trend_data = db.query(
            date_trunc.label('time_period'),
            func.count(WorkflowExecution.id).label('total'),
            func.sum(case((WorkflowExecution.status == ExecutionStatus.SUCCESS.value, 1), else_=0)).label('success'),
            func.sum(case((WorkflowExecution.status == ExecutionStatus.FAILED.value, 1), else_=0)).label('failed'),
            func.sum(case((WorkflowExecution.status == ExecutionStatus.TIMEOUT.value, 1), else_=0)).label('timeout'),
            func.avg(WorkflowExecution.duration_ms).label('avg_duration')
        ).filter(
            WorkflowExecution.created_at >= start_time
        ).group_by('time_period').order_by(asc('time_period')).all()
        
        labels = []
        total_data = []
        success_data = []
        failed_data = []
        timeout_data = []
        duration_data = []
        
        for row in trend_data:
            labels.append(str(row.time_period))
            total_data.append(row.total or 0)
            success_data.append(row.success or 0)
            failed_data.append(row.failed or 0)
            timeout_data.append(row.timeout or 0)
            duration_data.append(round(row.avg_duration, 2) if row.avg_duration else 0)
        
        return {
            "period": period,
            "labels": labels,
            "datasets": {
                "total": total_data,
                "success": success_data,
                "failed": failed_data,
                "timeout": timeout_data,
                "avg_duration_ms": duration_data
            }
        }
    
    # ==================== 节点执行统计 ====================
    
    @staticmethod
    def get_node_execution_stats(db: Session, limit: int = 20) -> Dict[str, Any]:
        """获取节点执行统计"""
        # 各类型节点执行次数和平均耗时
        node_type_stats = db.query(
            NodeExecution.node_type,
            func.count(NodeExecution.id).label('execution_count'),
            func.avg(NodeExecution.duration_ms).label('avg_duration'),
            func.sum(case((NodeExecution.status == ExecutionStatus.FAILED.value, 1), else_=0)).label('fail_count'),
            func.sum(case((NodeExecution.status == ExecutionStatus.SUCCESS.value, 1), else_=0)).label('success_count')
        ).group_by(NodeExecution.node_type).order_by(desc('execution_count')).limit(limit).all()
        
        node_types = []
        execution_counts = []
        avg_durations = []
        fail_rates = []
        
        for row in node_type_stats:
            node_types.append(row.node_type)
            execution_counts.append(row.execution_count)
            avg_durations.append(round(row.avg_duration, 2) if row.avg_duration else 0)
            
            fail_rate = (row.fail_count / row.execution_count * 100) if row.execution_count > 0 else 0
            fail_rates.append(round(fail_rate, 2))
        
        # 节点失败率排行
        node_failure_ranking = []
        for row in node_type_stats:
            if row.execution_count > 0:
                fail_rate = (row.fail_count / row.execution_count * 100)
                node_failure_ranking.append({
                    "node_type": row.node_type,
                    "execution_count": row.execution_count,
                    "fail_count": row.fail_count,
                    "fail_rate": round(fail_rate, 2),
                    "avg_duration_ms": round(row.avg_duration, 2) if row.avg_duration else 0
                })
        
        # 按失败率排序
        node_failure_ranking.sort(key=lambda x: x['fail_rate'], reverse=True)
        
        return {
            "node_type_distribution": {
                "labels": node_types,
                "execution_counts": execution_counts,
                "avg_durations": avg_durations,
                "fail_rates": fail_rates
            },
            "failure_ranking": node_failure_ranking[:10]  # Top 10
        }
    
    @staticmethod
    def get_slow_nodes(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """获取执行最慢的节点"""
        slow_nodes = db.query(
            NodeExecution.node_type,
            NodeExecution.node_name,
            func.avg(NodeExecution.duration_ms).label('avg_duration'),
            func.max(NodeExecution.duration_ms).label('max_duration'),
            func.count(NodeExecution.id).label('execution_count')
        ).filter(
            NodeExecution.duration_ms.isnot(None)
        ).group_by(NodeExecution.node_type, NodeExecution.node_name).order_by(
            desc('avg_duration')
        ).limit(limit).all()
        
        result = []
        for row in slow_nodes:
            result.append({
                "node_type": row.node_type,
                "node_name": row.node_name or row.node_type,
                "avg_duration_ms": round(row.avg_duration, 2),
                "max_duration_ms": row.max_duration,
                "execution_count": row.execution_count
            })
        
        return result
    
    # ==================== 热门工作流 ====================
    
    @staticmethod
    def get_popular_workflows(db: Session, limit: int = 10) -> Dict[str, Any]:
        """获取最活跃的工作流"""
        # 执行次数最多的工作流
        popular_workflows = db.query(
            Workflow.id,
            Workflow.name,
            Workflow.execution_count,
            Workflow.success_count,
            Workflow.fail_count,
            Workflow.created_at
        ).order_by(desc(Workflow.execution_count)).limit(limit).all()
        
        most_executed = []
        for wf in popular_workflows:
            success_rate = (wf.success_count / wf.execution_count * 100) if wf.execution_count > 0 else 0
            most_executed.append({
                "id": str(wf.id),
                "name": wf.name,
                "execution_count": wf.execution_count,
                "success_count": wf.success_count,
                "fail_count": wf.fail_count,
                "success_rate": round(success_rate, 1),
                "created_at": wf.created_at.isoformat() if wf.created_at else None
            })
        
        # 最近执行的工作流
        recent_executions = db.query(
            WorkflowExecution.workflow_id,
            Workflow.name.label('workflow_name'),
            func.max(WorkflowExecution.created_at).label('last_executed_at'),
            func.count(WorkflowExecution.id).label('recent_count')
        ).join(Workflow, WorkflowExecution.workflow_id == Workflow.id).filter(
            WorkflowExecution.created_at >= datetime.utcnow() - timedelta(days=7)
        ).group_by(WorkflowExecution.workflow_id, Workflow.name).order_by(
            desc('last_executed_at')
        ).limit(limit).all()
        
        recent_workflows = []
        for row in recent_executions:
            recent_workflows.append({
                "id": str(row.workflow_id),
                "name": row.workflow_name,
                "last_executed_at": row.last_executed_at.isoformat() if row.last_executed_at else None,
                "recent_executions": row.recent_count
            })
        
        return {
            "most_executed": most_executed,
            "recently_executed": recent_workflows
        }
    
    # ==================== 异常告警 ====================
    
    @staticmethod
    def get_alerts(
        db: Session,
        failed_limit: int = 10,
        timeout_threshold: int = 300  # 5分钟超时
    ) -> Dict[str, Any]:
        """获取异常告警信息"""
        now = datetime.utcnow()
        
        # 1. 失败的执行
        failed_executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.status == ExecutionStatus.FAILED.value
        ).order_by(desc(WorkflowExecution.created_at)).limit(failed_limit).all()
        
        failed_list = []
        for exec in failed_executions:
            workflow = db.query(Workflow).filter(Workflow.id == exec.workflow_id).first()
            failed_list.append({
                "id": str(exec.id),
                "workflow_id": str(exec.workflow_id),
                "workflow_name": workflow.name if workflow else "未知工作流",
                "status": exec.status,
                "error_message": exec.error_message,
                "created_at": exec.created_at.isoformat() if exec.created_at else None,
                "started_at": exec.started_at.isoformat() if exec.started_at else None,
                "duration_ms": exec.duration_ms
            })
        
        # 2. 超时的工作流（运行时间超过阈值）
        timeout_threshold_time = now - timedelta(seconds=timeout_threshold)
        long_running = db.query(WorkflowExecution).filter(
            WorkflowExecution.status == ExecutionStatus.RUNNING.value,
            WorkflowExecution.started_at < timeout_threshold_time
        ).order_by(asc(WorkflowExecution.started_at)).all()
        
        timeout_list = []
        for exec in long_running:
            workflow = db.query(Workflow).filter(Workflow.id == exec.workflow_id).first()
            running_duration = (now - exec.started_at).total_seconds() * 1000 if exec.started_at else 0
            timeout_list.append({
                "id": str(exec.id),
                "workflow_id": str(exec.workflow_id),
                "workflow_name": workflow.name if workflow else "未知工作流",
                "started_at": exec.started_at.isoformat() if exec.started_at else None,
                "running_duration_ms": round(running_duration, 2),
                "trigger_type": exec.trigger_type
            })
        
        # 3. 错误率过高的工作流（最近24小时失败率超过50%且执行次数超过5次）
        day_ago = now - timedelta(days=1)
        high_error_workflows = db.query(
            WorkflowExecution.workflow_id,
            Workflow.name.label('workflow_name'),
            func.count(WorkflowExecution.id).label('total_count'),
            func.sum(case((WorkflowExecution.status == ExecutionStatus.FAILED.value, 1), else_=0)).label('fail_count')
        ).join(Workflow, WorkflowExecution.workflow_id == Workflow.id).filter(
            WorkflowExecution.created_at >= day_ago
        ).group_by(WorkflowExecution.workflow_id, Workflow.name).having(
            func.count(WorkflowExecution.id) >= 5
        ).all()
        
        high_error_list = []
        for row in high_error_workflows:
            fail_rate = (row.fail_count / row.total_count * 100) if row.total_count > 0 else 0
            if fail_rate > 50:
                high_error_list.append({
                    "workflow_id": str(row.workflow_id),
                    "workflow_name": row.workflow_name,
                    "total_executions": row.total_count,
                    "fail_count": row.fail_count,
                    "fail_rate": round(fail_rate, 1)
                })
        
        # 按失败率排序
        high_error_list.sort(key=lambda x: x['fail_rate'], reverse=True)
        
        return {
            "failed_executions": failed_list,
            "timeout_executions": timeout_list,
            "high_error_rate_workflows": high_error_list[:10],
            "summary": {
                "failed_count": len(failed_list),
                "timeout_count": len(timeout_list),
                "high_error_count": len(high_error_list)
            }
        }
    
    # ==================== 综合监控数据 ====================
    
    @classmethod
    def get_full_dashboard_data(cls, db: Session) -> Dict[str, Any]:
        """获取完整的Dashboard数据（带缓存）"""
        cache_key = "full_dashboard_data"
        cached = cls._get_cached(cache_key)
        if cached:
            return cached
        
        data = {
            "basic_stats": cls.get_basic_stats(db),
            "execution_stats": cls.get_execution_stats_by_period(db),
            "realtime": cls.get_realtime_executions(db),
            "trend": cls.get_execution_trend(db, period="day", days=7),
            "node_stats": cls.get_node_execution_stats(db),
            "popular_workflows": cls.get_popular_workflows(db),
            "alerts": cls.get_alerts(db)
        }
        
        cls._set_cached(cache_key, data, ttl=30)
        return data
    
    @classmethod
    def get_system_health(cls, db: Session) -> Dict[str, Any]:
        """获取系统健康状态"""
        now = datetime.utcnow()
        
        # 检查最近5分钟的执行情况
        five_min_ago = now - timedelta(minutes=5)
        recent_executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.created_at >= five_min_ago
        ).count()
        
        # 检查当前运行中的执行
        running_count = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.status == ExecutionStatus.RUNNING.value
        ).scalar() or 0
        
        # 检查最近的失败
        recent_fails = db.query(func.count(WorkflowExecution.id)).filter(
            WorkflowExecution.status == ExecutionStatus.FAILED.value,
            WorkflowExecution.created_at >= five_min_ago
        ).scalar() or 0
        
        # 计算健康度
        if recent_executions > 0:
            fail_rate = recent_fails / recent_executions * 100
            if fail_rate < 5:
                health_status = "healthy"
                health_score = 95
            elif fail_rate < 20:
                health_status = "warning"
                health_score = 75
            else:
                health_status = "critical"
                health_score = 50
        else:
            health_status = "healthy"
            health_score = 100
        
        return {
            "status": health_status,
            "score": health_score,
            "recent_activity": {
                "executions_in_5m": recent_executions,
                "fails_in_5m": recent_fails,
                "running_now": running_count
            },
            "timestamp": now.isoformat()
        }
