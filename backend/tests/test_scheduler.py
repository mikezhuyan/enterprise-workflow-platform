"""
定时调度器测试
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.scheduler_service import WorkflowScheduleService, SchedulerService
from app.schemas.workflow import WorkflowScheduleCreate


class TestSchedulerService:
    """测试定时调度服务"""

    def test_create_schedule(self, db_session, test_workflow, test_user):
        """测试创建定时任务"""
        schedule_data = WorkflowScheduleCreate(
            workflow_id=test_workflow.id,
            name="测试定时任务",
            cron_expression="0 9 * * *",  # 每天9点
            timezone="Asia/Shanghai",
            input_data={"test": "value"}
        )
        
        schedule = WorkflowScheduleService.create_schedule(
            db_session, 
            schedule_data, 
            test_user.id
        )
        
        assert schedule.name == "测试定时任务"
        assert schedule.cron_expression == "0 9 * * *"
        assert schedule.timezone == "Asia/Shanghai"
        assert schedule.is_active is True
        assert schedule.created_by == test_user.id

    def test_validate_cron_expression(self):
        """测试Cron表达式验证"""
        # 有效表达式
        valid_crons = [
            "0 9 * * *",      # 每天9点
            "*/5 * * * *",    # 每5分钟
            "0 0 * * 0",      # 每周日
            "0 0 1 * *",      # 每月1日
        ]
        
        for cron in valid_crons:
            result = WorkflowScheduleService.validate_cron(cron)
            assert result is True, f"{cron} 应该是有效的"
        
        # 无效表达式
        invalid_crons = [
            "invalid",
            "60 * * * *",     # 分钟超出范围
            "0 25 * * *",     # 小时超出范围
            "",
        ]
        
        for cron in invalid_crons:
            result = WorkflowScheduleService.validate_cron(cron)
            assert result is False, f"{cron} 应该是无效的"

    def test_list_schedules(self, db_session, test_workflow, test_user):
        """测试获取定时任务列表"""
        # 创建测试数据
        for i in range(3):
            schedule_data = WorkflowScheduleCreate(
                workflow_id=test_workflow.id,
                name=f"定时任务{i}",
                cron_expression=f"{i} * * * *"
            )
            WorkflowScheduleService.create_schedule(
                db_session, schedule_data, test_user.id
            )
        
        schedules, total = WorkflowScheduleService.list_schedules(
            db_session, workflow_id=test_workflow.id
        )
        
        assert total == 3
        assert len(schedules) == 3

    def test_update_schedule(self, db_session, test_workflow, test_user):
        """测试更新定时任务"""
        # 创建任务
        schedule_data = WorkflowScheduleCreate(
            workflow_id=test_workflow.id,
            name="原名称",
            cron_expression="0 9 * * *"
        )
        schedule = WorkflowScheduleService.create_schedule(
            db_session, schedule_data, test_user.id
        )
        
        # 更新
        update_data = {"name": "新名称", "cron_expression": "0 10 * * *"}
        updated = WorkflowScheduleService.update_schedule(
            db_session, schedule.id, update_data
        )
        
        assert updated.name == "新名称"
        assert updated.cron_expression == "0 10 * * *"

    def test_pause_resume_schedule(self, db_session, test_workflow, test_user):
        """测试暂停和恢复定时任务"""
        schedule_data = WorkflowScheduleCreate(
            workflow_id=test_workflow.id,
            name="测试任务",
            cron_expression="0 9 * * *"
        )
        schedule = WorkflowScheduleService.create_schedule(
            db_session, schedule_data, test_user.id
        )
        
        # 暂停
        paused = WorkflowScheduleService.pause_schedule(db_session, schedule.id)
        assert paused.is_active is False
        
        # 恢复
        resumed = WorkflowScheduleService.resume_schedule(db_session, schedule.id)
        assert resumed.is_active is True

    def test_delete_schedule(self, db_session, test_workflow, test_user):
        """测试删除定时任务"""
        schedule_data = WorkflowScheduleCreate(
            workflow_id=test_workflow.id,
            name="待删除任务",
            cron_expression="0 9 * * *"
        )
        schedule = WorkflowScheduleService.create_schedule(
            db_session, schedule_data, test_user.id
        )
        
        # 删除
        result = WorkflowScheduleService.delete_schedule(db_session, schedule.id)
        assert result is True
        
        # 验证已删除
        deleted = WorkflowScheduleService.get_schedule(db_session, schedule.id)
        assert deleted is None


class TestSchedulerExecution:
    """测试调度器执行"""

    @pytest.mark.asyncio
    async def test_execute_scheduled_workflow(self, db_session, test_workflow):
        """测试定时执行工作流"""
        from app.workflow.engine import WorkflowEngine
        
        # Mock 工作流引擎
        with patch.object(WorkflowEngine, 'execute_workflow') as mock_execute:
            mock_execute.return_value = {
                "status": "success",
                "execution_id": "test-uuid"
            }
            
            # 执行定时任务
            await SchedulerService.execute_scheduled_workflow(
                str(test_workflow.id),
                {"test": "data"},
                "schedule-uuid"
            )
            
            # 验证引擎被调用
            mock_execute.assert_called_once()

    def test_calculate_next_run(self):
        """测试计算下次执行时间"""
        from croniter import croniter
        
        # 每天9点
        cron = "0 9 * * *"
        iter = croniter(cron, datetime.now())
        next_run = iter.get_next(datetime)
        
        assert next_run.hour == 9
        assert next_run.minute == 0
        
        # 每5分钟
        cron = "*/5 * * * *"
        iter = croniter(cron, datetime.now())
        next_run = iter.get_next(datetime)
        
        assert next_run.minute % 5 == 0
