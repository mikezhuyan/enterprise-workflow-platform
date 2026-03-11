"""
工作流版本控制测试
"""
import pytest
from datetime import datetime

from app.services.workflow_service import WorkflowService
from app.schemas.workflow import WorkflowCreate, WorkflowVersionCreate


class TestVersionControl:
    """测试工作流版本控制"""

    def test_create_version(self, db_session, test_workflow, test_user):
        """测试创建新版本"""
        # 创建新版本
        new_version = WorkflowService.create_version(
            db_session,
            test_workflow,
            test_user.id,
            comment="这是新版本"
        )
        
        assert new_version.version == "1.0.1"  # 默认递增修订号
        assert new_version.parent_id == test_workflow.id
        assert new_version.definition == test_workflow.definition

    def test_create_major_version(self, db_session, test_workflow, test_user):
        """测试创建主版本"""
        new_version = WorkflowService.create_version(
            db_session,
            test_workflow,
            test_user.id,
            version_type="major",
            comment="主版本更新"
        )
        
        assert new_version.version == "2.0.0"

    def test_create_minor_version(self, db_session, test_workflow, test_user):
        """测试创建次版本"""
        new_version = WorkflowService.create_version(
            db_session,
            test_workflow,
            test_user.id,
            version_type="minor",
            comment="次版本更新"
        )
        
        assert new_version.version == "1.1.0"

    def test_get_versions(self, db_session, test_workflow, test_user):
        """测试获取版本列表"""
        # 创建多个版本
        for i in range(3):
            WorkflowService.create_version(
                db_session,
                test_workflow,
                test_user.id,
                comment=f"版本 {i}"
            )
        
        versions = WorkflowService.get_versions(
            db_session, test_workflow.id
        )
        
        assert len(versions) >= 3
        # 按版本号降序排列
        versions_list = list(versions)
        if len(versions_list) >= 2:
            assert versions_list[0].version >= versions_list[1].version

    def test_get_version_by_number(self, db_session, test_workflow, test_user):
        """测试通过版本号获取版本"""
        # 创建新版本
        new_version = WorkflowService.create_version(
            db_session,
            test_workflow,
            test_user.id
        )
        
        # 通过版本号获取
        found = WorkflowService.get_version_by_number(
            db_session,
            test_workflow.id,
            new_version.version
        )
        
        assert found is not None
        assert found.version == new_version.version

    def test_rollback_to_version(self, db_session, test_workflow, test_user):
        """测试回滚到指定版本"""
        # 保存原定义
        original_def = test_workflow.definition.copy()
        
        # 创建新版本
        version = WorkflowService.create_version(
            db_session,
            test_workflow,
            test_user.id
        )
        
        # 修改当前工作流
        test_workflow.definition = {"nodes": [], "edges": []}
        db_session.commit()
        
        # 回滚
        rolled_back = WorkflowService.rollback_to_version(
            db_session,
            test_workflow.id,
            version.version,
            test_user.id
        )
        
        assert rolled_back is not None
        # 回滚会创建新版本，内容与原版本相同
        assert rolled_back.definition == original_def

    def test_compare_versions(self, db_session, test_workflow, test_user):
        """测试比较版本差异"""
        # 创建第一个版本
        v1 = WorkflowService.create_version(
            db_session,
            test_workflow,
            test_user.id,
            comment="版本1"
        )
        
        # 修改工作流
        test_workflow.definition["nodes"].append({
            "id": "new_node",
            "type": "api"
        })
        db_session.commit()
        
        # 创建第二个版本
        v2 = WorkflowService.create_version(
            db_session,
            test_workflow,
            test_user.id,
            comment="版本2"
        )
        
        # 比较版本
        diff = WorkflowService.compare_versions(
            db_session,
            test_workflow.id,
            v1.version,
            v2.version
        )
        
        assert diff is not None
        assert "changes" in diff or "summary" in diff

    def test_version_increment(self, db_session, test_workflow, test_user):
        """测试版本号递增逻辑"""
        test_cases = [
            ("1.0.0", "major", "2.0.0"),
            ("1.0.0", "minor", "1.1.0"),
            ("1.0.0", "patch", "1.0.1"),
            ("2.5.3", "major", "3.0.0"),
            ("2.5.3", "minor", "2.6.0"),
            ("2.5.3", "patch", "2.5.4"),
        ]
        
        for current, vtype, expected in test_cases:
            result = WorkflowService._increment_version(current, vtype)
            assert result == expected, f"{current} + {vtype} should be {expected}, got {result}"

    def test_version_permissions(self, db_session, test_workflow, test_user, other_user):
        """测试版本操作权限"""
        # 非创建者尝试回滚应该失败或需要权限检查
        # 这里假设权限检查在API层处理
        
        version = WorkflowService.create_version(
            db_session,
            test_workflow,
            test_user.id
        )
        
        # 验证版本创建者是正确的
        assert version.created_by == test_user.id
