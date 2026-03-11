"""
Webhook服务
"""
import hmac
import hashlib
import uuid as uuid_module
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.workflow import Webhook, WebhookLog, Workflow, WorkflowExecution, ExecutionStatus
from app.schemas.webhook import WebhookCreate, WebhookUpdate
from app.core.config import settings


class WebhookService:
    """Webhook服务"""
    
    @staticmethod
    def generate_secret() -> str:
        """生成签名密钥"""
        return "whsec_" + hashlib.sha256(
            uuid_module.uuid4().bytes + uuid_module.uuid4().bytes
        ).hexdigest()[:32]
    
    @staticmethod
    def get_webhook_url(webhook_uuid: UUID) -> str:
        """生成Webhook URL"""
        # 使用配置中的服务器地址
        base_url = f"http://{settings.HOST}:{settings.PORT}"
        if settings.HOST == "0.0.0.0":
            base_url = f"http://localhost:{settings.PORT}"
        return f"{base_url}/webhooks/{webhook_uuid}"
    
    @staticmethod
    def verify_signature(payload: bytes, secret: str, signature: str) -> bool:
        """
        验证Webhook签名
        
        支持格式:
        - X-Webhook-Signature: sha256=<hex_digest>
        - X-Hub-Signature-256: sha256=<hex_digest>
        """
        if not signature:
            return False
        
        # 提取签名值
        if "=" in signature:
            _, sig_value = signature.split("=", 1)
        else:
            sig_value = signature
        
        # 计算期望的签名
        expected = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # 使用constant_time_compare防止时序攻击
        return hmac.compare_digest(sig_value, expected)
    
    @staticmethod
    def generate_signature(payload: bytes, secret: str) -> str:
        """生成Webhook签名"""
        sig = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={sig}"
    
    @classmethod
    def get_by_id(cls, db: Session, webhook_id: UUID) -> Optional[Webhook]:
        """根据ID获取Webhook"""
        return db.query(Webhook).filter(Webhook.id == webhook_id).first()
    
    @classmethod
    def get_by_uuid(cls, db: Session, webhook_uuid: UUID) -> Optional[Webhook]:
        """根据UUID获取Webhook"""
        return db.query(Webhook).filter(Webhook.uuid == webhook_uuid).first()
    
    @classmethod
    def get_by_workflow(cls, db: Session, workflow_id: UUID, skip: int = 0, limit: int = 20) -> Tuple[List[Webhook], int]:
        """获取工作流的所有Webhook"""
        query = db.query(Webhook).filter(Webhook.workflow_id == workflow_id)
        total = query.count()
        webhooks = query.order_by(Webhook.created_at.desc()).offset(skip).limit(limit).all()
        return webhooks, total
    
    @classmethod
    def create_webhook(
        cls,
        db: Session,
        workflow_id: UUID,
        webhook_data: WebhookCreate,
        user_id: UUID
    ) -> Tuple[Webhook, str]:
        """创建Webhook"""
        # 生成新的UUID和密钥
        webhook_uuid = uuid_module.uuid4()
        secret = cls.generate_secret()
        
        webhook = Webhook(
            workflow_id=workflow_id,
            uuid=webhook_uuid,
            name=webhook_data.name,
            description=webhook_data.description,
            secret=secret,
            require_signature=webhook_data.require_signature,
            rate_limit=webhook_data.rate_limit,
            is_active=True,
            call_count=0,
            created_by=user_id,
        )
        
        db.add(webhook)
        db.commit()
        db.refresh(webhook)
        
        # 生成Webhook URL
        webhook_url = cls.get_webhook_url(webhook_uuid)
        
        return webhook, webhook_url
    
    @classmethod
    def update_webhook(
        cls,
        db: Session,
        webhook: Webhook,
        webhook_data: WebhookUpdate
    ) -> Webhook:
        """更新Webhook"""
        update_data = webhook_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(webhook, field, value)
        
        webhook.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(webhook)
        return webhook
    
    @classmethod
    def delete_webhook(cls, db: Session, webhook: Webhook) -> None:
        """删除Webhook"""
        db.delete(webhook)
        db.commit()
    
    @classmethod
    def regenerate_webhook(cls, db: Session, webhook: Webhook) -> Tuple[Webhook, str]:
        """重新生成Webhook UUID和密钥"""
        # 生成新的UUID和密钥
        webhook.uuid = uuid_module.uuid4()
        webhook.secret = cls.generate_secret()
        webhook.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(webhook)
        
        webhook_url = cls.get_webhook_url(webhook.uuid)
        return webhook, webhook_url
    
    @classmethod
    def check_rate_limit(cls, db: Session, webhook: Webhook) -> bool:
        """检查速率限制"""
        if webhook.rate_limit <= 0:
            return True
        
        # 计算最近一分钟的请求数
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_calls = db.query(func.count(WebhookLog.id)).filter(
            WebhookLog.webhook_id == webhook.id,
            WebhookLog.created_at >= one_minute_ago
        ).scalar()
        
        return recent_calls < webhook.rate_limit
    
    @classmethod
    def trigger_workflow(
        cls,
        db: Session,
        webhook: Webhook,
        request_data: Dict[str, Any],
        headers: Dict[str, str],
        client_ip: str,
        request_body: bytes
    ) -> Tuple[bool, Optional[UUID], Optional[str]]:
        """
        触发工作流执行
        
        Returns:
            (success, execution_id, error_message)
        """
        from app.workflow.engine import WorkflowEngine
        from app.services.workflow_service import WorkflowService
        
        # 验证签名
        signature_valid = None
        if webhook.require_signature:
            signature = headers.get("x-webhook-signature") or headers.get("x-hub-signature-256")
            if not signature:
                return False, None, "Missing signature header"
            
            signature_valid = cls.verify_signature(request_body, webhook.secret, signature)
            if not signature_valid:
                return False, None, "Invalid signature"
        
        # 检查速率限制
        if not cls.check_rate_limit(db, webhook):
            return False, None, "Rate limit exceeded"
        
        # 检查Webhook是否激活
        if not webhook.is_active:
            return False, None, "Webhook is not active"
        
        # 检查工作流状态
        workflow = db.query(Workflow).filter(Workflow.id == webhook.workflow_id).first()
        if not workflow:
            return False, None, "Workflow not found"
        
        if workflow.status != "published":
            return False, None, "Workflow is not published"
        
        # 创建工作流引擎并执行
        engine = WorkflowEngine()
        
        # 准备输入数据
        input_data = {
            "webhook": {
                "id": str(webhook.id),
                "uuid": str(webhook.uuid),
                "name": webhook.name,
            },
            "request": {
                "method": headers.get("method", "POST"),
                "headers": headers,
                "body": request_data,
                "ip": client_ip,
            }
        }
        
        try:
            # 创建执行记录
            execution = WorkflowExecution(
                workflow_id=webhook.workflow_id,
                status=ExecutionStatus.RUNNING.value,
                input_data=input_data,
                trigger_type="webhook",
                started_at=datetime.utcnow(),
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            # 更新Webhook统计
            webhook.call_count += 1
            webhook.last_called_at = datetime.utcnow()
            db.commit()
            
            # TODO: 实际执行工作流 (可以同步或异步)
            # 这里我们先创建执行记录，实际执行可以在后台任务中完成
            
            return True, execution.id, None
            
        except Exception as e:
            return False, None, str(e)
    
    @classmethod
    def create_log(
        cls,
        db: Session,
        webhook_id: UUID,
        request_method: str,
        request_headers: Dict[str, Any],
        request_body: str,
        request_ip: str,
        response_status: int,
        response_body: str,
        signature_valid: Optional[bool],
        execution_id: Optional[UUID],
        error_message: Optional[str],
        duration_ms: int
    ) -> WebhookLog:
        """创建Webhook调用日志"""
        log = WebhookLog(
            webhook_id=webhook_id,
            request_method=request_method,
            request_headers=request_headers,
            request_body=request_body,
            request_ip=request_ip,
            response_status=response_status,
            response_body=response_body,
            signature_valid=signature_valid,
            execution_id=execution_id,
            error_message=error_message,
            duration_ms=duration_ms,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @classmethod
    def get_logs(
        cls,
        db: Session,
        webhook_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[WebhookLog], int]:
        """获取Webhook调用日志"""
        query = db.query(WebhookLog).filter(WebhookLog.webhook_id == webhook_id)
        total = query.count()
        logs = query.order_by(WebhookLog.created_at.desc()).offset(skip).limit(limit).all()
        return logs, total
