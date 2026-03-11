"""
Webhook触发器测试
"""
import pytest
import uuid
import hmac
import hashlib
import json
from unittest.mock import Mock, patch

from app.services.webhook_service import WebhookService
from app.schemas.webhook import WebhookCreate, WebhookUpdate


class TestWebhookService:
    """测试Webhook服务"""

    def test_create_webhook(self, db_session, test_workflow, test_user):
        """测试创建Webhook"""
        webhook_data = WebhookCreate(
            workflow_id=test_workflow.id,
            name="测试Webhook",
            description="用于测试的Webhook"
        )
        
        webhook = WebhookService.create_webhook(
            db_session,
            webhook_data,
            test_user.id
        )
        
        assert webhook.name == "测试Webhook"
        assert webhook.workflow_id == test_workflow.id
        assert webhook.uuid is not None
        assert webhook.secret is not None
        assert webhook.is_active is True

    def test_generate_webhook_url(self, db_session, test_workflow, test_user):
        """测试生成Webhook URL"""
        webhook_data = WebhookCreate(
            workflow_id=test_workflow.id,
            name="测试Webhook"
        )
        webhook = WebhookService.create_webhook(
            db_session, webhook_data, test_user.id
        )
        
        # 生成URL
        base_url = "https://example.com"
        url = WebhookService.get_webhook_url(webhook.uuid, base_url)
        
        assert webhook.uuid in url
        assert base_url in url

    def test_regenerate_webhook(self, db_session, test_workflow, test_user):
        """测试重新生成Webhook"""
        webhook_data = WebhookCreate(name="测试Webhook")
        webhook = WebhookService.create_webhook(
            db_session, webhook_data, test_user.id
        )
        
        old_uuid = webhook.uuid
        old_secret = webhook.secret
        
        # 重新生成
        regenerated = WebhookService.regenerate_webhook(
            db_session, webhook.id
        )
        
        assert regenerated.uuid != old_uuid
        assert regenerated.secret != old_secret
        assert regenerated.is_active is True

    def test_list_webhooks(self, db_session, test_workflow, test_user):
        """测试获取Webhook列表"""
        # 创建多个webhook
        for i in range(3):
            webhook_data = WebhookCreate(
                name=f"Webhook {i}",
                description=f"描述 {i}"
            )
            WebhookService.create_webhook(
                db_session, webhook_data, test_user.id
            )
        
        webhooks, total = WebhookService.list_webhooks(
            db_session, workflow_id=test_workflow.id
        )
        
        assert total == 3
        assert len(webhooks) == 3

    def test_update_webhook(self, db_session, test_workflow, test_user):
        """测试更新Webhook"""
        webhook_data = WebhookCreate(
            name="原名称",
            description="原描述"
        )
        webhook = WebhookService.create_webhook(
            db_session, webhook_data, test_user.id
        )
        
        # 更新
        update_data = WebhookUpdate(
            name="新名称",
            description="新描述",
            is_active=False
        )
        updated = WebhookService.update_webhook(
            db_session, webhook.id, update_data
        )
        
        assert updated.name == "新名称"
        assert updated.description == "新描述"
        assert updated.is_active is False

    def test_delete_webhook(self, db_session, test_workflow, test_user):
        """测试删除Webhook"""
        webhook_data = WebhookCreate(name="待删除")
        webhook = WebhookService.create_webhook(
            db_session, webhook_data, test_user.id
        )
        
        result = WebhookService.delete_webhook(db_session, webhook.id)
        assert result is True
        
        # 验证已删除
        deleted = WebhookService.get_webhook_by_id(db_session, webhook.id)
        assert deleted is None


class TestWebhookSignature:
    """测试Webhook签名验证"""

    def test_generate_signature(self):
        """测试生成签名"""
        secret = "test-secret"
        payload = json.dumps({"test": "data"})
        
        signature = WebhookService.generate_signature(payload, secret)
        
        assert signature is not None
        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_verify_signature(self):
        """测试验证签名"""
        secret = "test-secret"
        payload = json.dumps({"test": "data"})
        
        # 生成签名
        signature = WebhookService.generate_signature(payload, secret)
        
        # 验证正确签名
        is_valid = WebhookService.verify_signature(payload, signature, secret)
        assert is_valid is True
        
        # 验证错误签名
        is_valid = WebhookService.verify_signature(payload, "wrong-sig", secret)
        assert is_valid is False

    def test_signature_with_special_chars(self):
        """测试包含特殊字符的payload签名"""
        secret = "test-secret"
        payload = json.dumps({
            "message": "Hello 世界! 🌍",
            "special": "<>&\"'"
        })
        
        signature = WebhookService.generate_signature(payload, secret)
        is_valid = WebhookService.verify_signature(payload, signature, secret)
        
        assert is_valid is True


class TestWebhookTrigger:
    """测试Webhook触发"""

    @pytest.mark.asyncio
    async def test_trigger_workflow(self, db_session, test_workflow):
        """测试触发工作流执行"""
        from app.workflow.engine import WorkflowEngine
        
        # Mock 工作流引擎
        with patch.object(WorkflowEngine, 'execute_workflow') as mock_execute:
            mock_execute.return_value = {
                "status": "success",
                "execution_id": "test-uuid"
            }
            
            # 触发执行
            result = await WebhookService.trigger_workflow(
                db_session,
                str(test_workflow.id),
                {"payload": "test"}
            )
            
            assert result["status"] == "success"
            assert "execution_id" in result

    def test_get_webhook_by_uuid(self, db_session, test_workflow, test_user):
        """测试通过UUID获取Webhook"""
        webhook_data = WebhookCreate(name="测试")
        webhook = WebhookService.create_webhook(
            db_session, webhook_data, test_user.id
        )
        
        # 通过UUID获取
        found = WebhookService.get_webhook_by_uuid(db_session, webhook.uuid)
        
        assert found is not None
        assert found.id == webhook.id
        assert found.uuid == webhook.uuid

    def test_get_webhook_logs(self, db_session, test_workflow, test_user):
        """测试获取Webhook调用日志"""
        webhook_data = WebhookCreate(name="测试")
        webhook = WebhookService.create_webhook(
            db_session, webhook_data, test_user.id
        )
        
        # 创建日志
        WebhookService.create_log(
            db_session,
            webhook.id,
            request_headers={"Content-Type": "application/json"},
            request_body={"test": "data"},
            response_status=200,
            response_body={"result": "ok"},
            execution_time_ms=150
        )
        
        # 获取日志
        logs, total = WebhookService.get_logs(db_session, webhook.id)
        
        assert total == 1
        assert logs[0].response_status == 200
