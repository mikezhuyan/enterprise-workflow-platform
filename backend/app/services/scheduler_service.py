"""
定时调度服务
使用APScheduler实现定时任务调度
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID
import asyncio
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent

from app.models.workflow import WorkflowSchedule, Workflow, WorkflowExecution, ExecutionStatus
from app.schemas.workflow import WorkflowScheduleCreate, WorkflowScheduleUpdate
from app.core.config import settings


class SchedulerService:
    """定时调度服务"""
    
    _instance = None
    _scheduler: Optional[AsyncIOScheduler] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SchedulerService, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_scheduler(cls) -> Optional[AsyncIOScheduler]:
        """获取调度器实例"""
        return cls._scheduler
    
    @classmethod
    def initialize(cls, db_url: Optional[str] = None):
        """初始化调度器"""
        if cls._scheduler is not None:
            return
        
        # 配置job store
        jobstores = {}
        if db_url and not db_url.startswith('sqlite'):
            # 使用数据库存储job（PostgreSQL）
            jobstores['default'] = SQLAlchemyJobStore(url=db_url)
        
        # 创建异步调度器
        cls._scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            timezone='UTC'
        )
        
        # 添加事件监听
        cls._scheduler.add_listener(
            cls._on_job_executed,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        
        cls._scheduler.start()
        print("✅ 定时调度器初始化完成")
    
    @classmethod
    def shutdown(cls):
        """关闭调度器"""
        if cls._scheduler:
            cls._scheduler.shutdown(wait=False)
            cls._scheduler = None
            print("👋 定时调度器已关闭")
    
    @staticmethod
    def _on_job_executed(event: JobExecutionEvent):
        """任务执行完成回调"""
        if event.exception:
            print(f"❌ 定时任务执行失败: {event.job_id}, 错误: {event.exception}")
        else:
            print(f"✅ 定时任务执行成功: {event.job_id}")
    
    @staticmethod
    async def _execute_scheduled_workflow(schedule_id: str, workflow_id: str, input_data: Dict[str, Any]):
        """执行定时工作流"""
        from app.db.base import SessionLocal
        from app.workflow.engine import WorkflowEngine
        from app.services.workflow_service import WorkflowService
        
        db = SessionLocal()
        try:
            # 获取调度任务
            schedule = db.query(WorkflowSchedule).filter(
                WorkflowSchedule.id == UUID(schedule_id)
            ).first()
            
            if not schedule or not schedule.is_active:
                print(f"⏭️ 调度任务不存在或已停用: {schedule_id}")
                return
            
            # 获取工作流
            workflow = WorkflowService.get_by_id(db, UUID(workflow_id))
            if not workflow:
                print(f"❌ 工作流不存在: {workflow_id}")
                return
            
            # 更新上次执行时间
            schedule.last_run_at = datetime.utcnow()
            db.commit()
            
            # 创建执行记录
            execution = WorkflowService.create_execution(
                db, UUID(workflow_id), input_data, trigger_type="schedule"
            )
            
            # 执行工作流
            engine = WorkflowEngine()
            execution.status = ExecutionStatus.RUNNING.value
            execution.started_at = datetime.utcnow()
            db.commit()
            
            try:
                result = await engine.execute_workflow(
                    workflow.definition,
                    input_data,
                    str(execution.id)
                )
                
                # 更新执行结果
                execution.status = ExecutionStatus.SUCCESS.value if result.get("status") == "success" else ExecutionStatus.FAILED.value
                execution.output_data = result
                execution.completed_at = datetime.utcnow()
                
                if execution.started_at and execution.completed_at:
                    execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
                
                # 更新工作流统计
                workflow.execution_count += 1
                if execution.status == ExecutionStatus.SUCCESS.value:
                    workflow.success_count += 1
                else:
                    workflow.fail_count += 1
                
                db.commit()
                
            except Exception as e:
                execution.status = ExecutionStatus.FAILED.value
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                workflow.fail_count += 1
                db.commit()
                raise
                
        finally:
            db.close()
    
    @classmethod
    def add_schedule_job(cls, schedule: WorkflowSchedule) -> bool:
        """添加定时任务到调度器"""
        if not cls._scheduler or not schedule.is_active:
            return False
        
        job_id = f"schedule_{schedule.id}"
        
        try:
            # 移除已存在的任务
            if cls._scheduler.get_job(job_id):
                cls._scheduler.remove_job(job_id)
            
            # 解析cron表达式
            cron_parts = schedule.cron_expression.split()
            if len(cron_parts) != 5:
                print(f"❌ 无效的cron表达式: {schedule.cron_expression}")
                return False
            
            minute, hour, day, month, day_of_week = cron_parts
            
            # 创建cron触发器
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=schedule.timezone
            )
            
            # 添加任务
            cls._scheduler.add_job(
                func=cls._execute_scheduled_workflow,
                trigger=trigger,
                id=job_id,
                args=[str(schedule.id), str(schedule.workflow_id), schedule.input_data or {}],
                replace_existing=True,
                misfire_grace_time=3600  # 1小时的容错时间
            )
            
            # 更新下次执行时间
            next_run_time = cls._scheduler.get_job(job_id).next_run_time
            if next_run_time:
                schedule.next_run_at = next_run_time.replace(tzinfo=None)
            
            print(f"✅ 定时任务已添加: {job_id}, cron: {schedule.cron_expression}")
            return True
            
        except Exception as e:
            print(f"❌ 添加定时任务失败: {job_id}, 错误: {e}")
            return False
    
    @classmethod
    def remove_schedule_job(cls, schedule_id: UUID) -> bool:
        """从调度器移除定时任务"""
        if not cls._scheduler:
            return False
        
        job_id = f"schedule_{schedule_id}"
        
        try:
            if cls._scheduler.get_job(job_id):
                cls._scheduler.remove_job(job_id)
                print(f"✅ 定时任务已移除: {job_id}")
            return True
        except Exception as e:
            print(f"❌ 移除定时任务失败: {job_id}, 错误: {e}")
            return False
    
    @classmethod
    def pause_schedule_job(cls, schedule_id: UUID) -> bool:
        """暂停定时任务"""
        if not cls._scheduler:
            return False
        
        job_id = f"schedule_{schedule_id}"
        
        try:
            job = cls._scheduler.get_job(job_id)
            if job:
                cls._scheduler.pause_job(job_id)
                print(f"⏸️ 定时任务已暂停: {job_id}")
                return True
            return False
        except Exception as e:
            print(f"❌ 暂停定时任务失败: {job_id}, 错误: {e}")
            return False
    
    @classmethod
    def resume_schedule_job(cls, schedule_id: UUID) -> bool:
        """恢复定时任务"""
        if not cls._scheduler:
            return False
        
        job_id = f"schedule_{schedule_id}"
        
        try:
            job = cls._scheduler.get_job(job_id)
            if job:
                cls._scheduler.resume_job(job_id)
                print(f"▶️ 定时任务已恢复: {job_id}")
                return True
            return False
        except Exception as e:
            print(f"❌ 恢复定时任务失败: {job_id}, 错误: {e}")
            return False
    
    @classmethod
    def update_schedule_job(cls, schedule: WorkflowSchedule) -> bool:
        """更新定时任务"""
        if not schedule.is_active:
            # 如果任务被停用，直接移除
            return cls.remove_schedule_job(schedule.id)
        
        # 重新添加任务（会更新cron表达式等）
        return cls.add_schedule_job(schedule)
    
    @classmethod
    def load_all_schedules(cls, db: Session):
        """从数据库加载所有活动的定时任务"""
        if not cls._scheduler:
            return
        
        schedules = db.query(WorkflowSchedule).filter(
            WorkflowSchedule.is_active == True
        ).all()
        
        count = 0
        for schedule in schedules:
            if cls.add_schedule_job(schedule):
                count += 1
        
        print(f"✅ 已加载 {count} 个定时任务")


class WorkflowScheduleService:
    """工作流定时任务服务"""
    
    @staticmethod
    def get_by_id(db: Session, schedule_id: UUID) -> Optional[WorkflowSchedule]:
        """根据ID获取定时任务"""
        return db.query(WorkflowSchedule).filter(WorkflowSchedule.id == schedule_id).first()
    
    @staticmethod
    def list_by_workflow(
        db: Session,
        workflow_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> tuple:
        """获取工作流的定时任务列表"""
        query = db.query(WorkflowSchedule).filter(
            WorkflowSchedule.workflow_id == workflow_id
        )
        
        total = query.count()
        schedules = query.order_by(WorkflowSchedule.created_at.desc()).offset(skip).limit(limit).all()
        return schedules, total
    
    @staticmethod
    def create_schedule(
        db: Session,
        workflow_id: UUID,
        schedule_data: WorkflowScheduleCreate
    ) -> WorkflowSchedule:
        """创建定时任务"""
        schedule = WorkflowSchedule(
            workflow_id=workflow_id,
            cron_expression=schedule_data.cron_expression,
            timezone=schedule_data.timezone,
            input_data=schedule_data.input_data,
            is_active=True
        )
        
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        
        # 添加到调度器
        SchedulerService.add_schedule_job(schedule)
        
        return schedule
    
    @staticmethod
    def update_schedule(
        db: Session,
        schedule: WorkflowSchedule,
        schedule_data: WorkflowScheduleUpdate
    ) -> WorkflowSchedule:
        """更新定时任务"""
        update_data = schedule_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(schedule, field, value)
        
        schedule.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(schedule)
        
        # 更新调度器中的任务
        SchedulerService.update_schedule_job(schedule)
        
        return schedule
    
    @staticmethod
    def delete_schedule(db: Session, schedule: WorkflowSchedule) -> None:
        """删除定时任务"""
        # 从调度器移除
        SchedulerService.remove_schedule_job(schedule.id)
        
        db.delete(schedule)
        db.commit()
    
    @staticmethod
    def pause_schedule(db: Session, schedule: WorkflowSchedule) -> WorkflowSchedule:
        """暂停定时任务"""
        schedule.is_active = False
        schedule.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(schedule)
        
        # 暂停调度器中的任务
        SchedulerService.pause_schedule_job(schedule.id)
        
        return schedule
    
    @staticmethod
    def resume_schedule(db: Session, schedule: WorkflowSchedule) -> WorkflowSchedule:
        """恢复定时任务"""
        schedule.is_active = True
        schedule.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(schedule)
        
        # 恢复调度器中的任务
        SchedulerService.update_schedule_job(schedule)
        
        return schedule
