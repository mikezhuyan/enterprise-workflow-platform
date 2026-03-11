"""
审批流程节点测试
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from app.services.workflow_service import ApprovalTaskService
from app.models.workflow import ApprovalTask, ExecutionStatus


class TestApprovalTaskService:
    """测试审批任务服务"""

    def test_create_task(self, db_session, test_execution, test_user):
        """测试创建审批任务"""
        task = ApprovalTaskService.create_task(
            db_session,
            execution_id=test_execution.id,
            node_id="approval_1",
            node_name="经理审批",
            assignee_type="user",
            assignee_id=test_user.id
        )
        
        assert task.node_id == "approval_1"
        assert task.node_name == "经理审批"
        assert task.status == "pending"
        assert task.assignee_type == "user"
        assert task.assignee_id == test_user.id

    def test_list_pending_tasks(self, db_session, test_execution, test_user):
        """测试获取待审批列表"""
        # 创建多个审批任务
        for i in range(3):
            ApprovalTaskService.create_task(
                db_session,
                execution_id=test_execution.id,
                node_id=f"approval_{i}",
                node_name=f"审批{i}",
                assignee_type="user",
                assignee_id=test_user.id
            )
        
        tasks = ApprovalTaskService.list_pending_tasks(
            db_session,
            user_id=test_user.id
        )
        
        assert len(tasks) == 3

    def test_approve_task(self, db_session, test_execution, test_user):
        """测试审批通过"""
        task = ApprovalTaskService.create_task(
            db_session,
            execution_id=test_execution.id,
            node_id="approval_1",
            node_name="经理审批",
            assignee_type="user",
            assignee_id=test_user.id
        )
        
        # 审批通过
        approved = ApprovalTaskService.approve_task(
            db_session,
            task.id,
            user_id=test_user.id,
            comment="同意"
        )
        
        assert approved.status == "approved"
        assert approved.comment == "同意"
        assert approved.completed_by == test_user.id
        assert approved.completed_at is not None

    def test_reject_task(self, db_session, test_execution, test_user):
        """测试审批拒绝"""
        task = ApprovalTaskService.create_task(
            db_session,
            execution_id=test_execution.id,
            node_id="approval_1",
            node_name="经理审批",
            assignee_type="user",
            assignee_id=test_user.id
        )
        
        # 审批拒绝
        rejected = ApprovalTaskService.reject_task(
            db_session,
            task.id,
            user_id=test_user.id,
            comment="不符合要求"
        )
        
        assert rejected.status == "rejected"
        assert rejected.comment == "不符合要求"
        assert rejected.completed_by == test_user.id

    def test_transfer_task(self, db_session, test_execution, test_user, other_user):
        """测试转办"""
        task = ApprovalTaskService.create_task(
            db_session,
            execution_id=test_execution.id,
            node_id="approval_1",
            node_name="经理审批",
            assignee_type="user",
            assignee_id=test_user.id
        )
        
        # 转办给其他人
        transferred = ApprovalTaskService.transfer_task(
            db_session,
            task.id,
            from_user_id=test_user.id,
            to_user_id=other_user.id,
            comment="请帮忙审批"
        )
        
        assert transferred.status == "transferred"
        assert transferred.assignee_id == other_user.id
        assert transferred.comment == "请帮忙审批"

    def test_check_user_can_approve(self, db_session, test_execution, test_user, other_user):
        """测试检查用户是否有审批权限"""
        task = ApprovalTaskService.create_task(
            db_session,
            execution_id=test_execution.id,
            node_id="approval_1",
            node_name="经理审批",
            assignee_type="user",
            assignee_id=test_user.id
        )
        
        # 正确用户可以审批
        can_approve = ApprovalTaskService.check_user_can_approve(
            db_session, task.id, test_user.id
        )
        assert can_approve is True
        
        # 其他用户不能审批
        can_approve = ApprovalTaskService.check_user_can_approve(
            db_session, task.id, other_user.id
        )
        assert can_approve is False

    def test_get_task_by_execution_and_node(self, db_session, test_execution, test_user):
        """测试通过执行和节点获取任务"""
        task = ApprovalTaskService.create_task(
            db_session,
            execution_id=test_execution.id,
            node_id="approval_1",
            node_name="经理审批",
            assignee_type="user",
            assignee_id=test_user.id
        )
        
        found = ApprovalTaskService.get_task_by_execution_and_node(
            db_session,
            test_execution.id,
            "approval_1"
        )
        
        assert found is not None
        assert found.id == task.id

    def test_list_user_tasks(self, db_session, test_execution, test_user):
        """测试获取用户的所有审批任务"""
        # 创建待审批和已审批的任务
        task1 = ApprovalTaskService.create_task(
            db_session,
            execution_id=test_execution.id,
            node_id="approval_1",
            node_name="待审批",
            assignee_type="user",
            assignee_id=test_user.id
        )
        
        task2 = ApprovalTaskService.create_task(
            db_session,
            execution_id=test_execution.id,
            node_id="approval_2",
            node_name="已审批",
            assignee_type="user",
            assignee_id=test_user.id
        )
        ApprovalTaskService.approve_task(db_session, task2.id, test_user.id)
        
        # 获取所有任务
        all_tasks = ApprovalTaskService.list_user_tasks(
            db_session, user_id=test_user.id
        )
        assert len(all_tasks) == 2
        
        # 获取待审批
        pending_tasks = ApprovalTaskService.list_user_tasks(
            db_session, user_id=test_user.id, status="pending"
        )
        assert len(pending_tasks) == 1
        
        # 获取已审批
        approved_tasks = ApprovalTaskService.list_user_tasks(
            db_session, user_id=test_user.id, status="approved"
        )
        assert len(approved_tasks) == 1

    def test_approval_with_role_assignee(self, db_session, test_execution):
        """测试按角色指派审批"""
        role_id = "role_manager"  # 假设的角色ID
        
        task = ApprovalTaskService.create_task(
            db_session,
            execution_id=test_execution.id,
            node_id="approval_1",
            node_name="经理审批",
            assignee_type="role",
            assignee_id=role_id
        )
        
        assert task.assignee_type == "role"
        assert task.assignee_id == role_id
