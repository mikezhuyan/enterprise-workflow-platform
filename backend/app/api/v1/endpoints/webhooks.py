"""
Webhook API端点
"""
import time
import json
from typing import Optional, Any
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.security import get_current_user
from app.services.webhook_service import WebhookService
from app.schemas.webhook import (
    WebhookCreate, WebhookUpdate, WebhookResponse, WebhookListResponse,
    WebhookDetailResponse, WebhookRegenerateResponse, WebhookTriggerResponse,
    WebhookLogResponse, WebhookLogListResponse
)
from app.schemas.user import PaginatedResponse
from app.models.user import User
from app.models.workflow import Webhook

# ============ 需要认证的路由器 ============

# 工作流相关的 Webhook 管理 (前缀: /workflows)
workflow_router = APIRouter()

# 独立的 Webhook 管理 (前缀: /webhooks)
webhook_router = APIRouter()

# ============ 公共路由器 (无需认证) ============

# 公共 Webhook 触发端点 (前缀: /webhooks)
public_router = APIRouter()


# ============ 工作流Webhook管理 ============

@workflow_router.get("/{workflow_id}/webhooks", response_model=PaginatedResponse)
def list_workflow_webhooks(
    workflow_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取工作流的Webhook列表"""
    # 检查工作流是否存在
    from app.services.workflow_service import WorkflowService
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限
    if workflow.created_by != current_user.id and not current_user.is_superuser:
        # 检查是否是租户内用户
        if workflow.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="无权访问此工作流")
    
    skip = (page - 1) * page_size
    webhooks, total = WebhookService.get_by_workflow(db, workflow_id, skip=skip, limit=page_size)
    
    webhook_list = [WebhookListResponse.model_validate(w).model_dump() for w in webhooks]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "data": webhook_list
    }


@workflow_router.post("/{workflow_id}/webhooks", response_model=WebhookDetailResponse, status_code=status.HTTP_201_CREATED)
def create_webhook(
    workflow_id: UUID,
    webhook_data: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为工作流创建Webhook"""
    # 检查工作流是否存在
    from app.services.workflow_service import WorkflowService
    workflow = WorkflowService.get_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查权限
    if workflow.created_by != current_user.id and not current_user.is_superuser:
        if workflow.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="无权为此工作流创建Webhook")
    
    webhook, webhook_url = WebhookService.create_webhook(
        db, workflow_id, webhook_data, current_user.id
    )
    
    response_data = WebhookResponse.model_validate(webhook).model_dump()
    response_data["webhook_url"] = webhook_url
    
    return response_data


@workflow_router.get("/{workflow_id}/webhooks/{webhook_id}", response_model=WebhookDetailResponse)
def get_webhook(
    workflow_id: UUID,
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取Webhook详情"""
    webhook = WebhookService.get_by_id(db, webhook_id)
    if not webhook or webhook.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 检查权限
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        workflow = webhook.workflow
        if workflow and workflow.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="无权访问此Webhook")
    
    response_data = WebhookResponse.model_validate(webhook).model_dump()
    response_data["webhook_url"] = WebhookService.get_webhook_url(webhook.uuid)
    
    return response_data


@workflow_router.put("/{workflow_id}/webhooks/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    workflow_id: UUID,
    webhook_id: UUID,
    webhook_data: WebhookUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新Webhook"""
    webhook = WebhookService.get_by_id(db, webhook_id)
    if not webhook or webhook.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 检查权限
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权修改此Webhook")
    
    updated_webhook = WebhookService.update_webhook(db, webhook, webhook_data)
    return updated_webhook


@workflow_router.delete("/{workflow_id}/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(
    workflow_id: UUID,
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除Webhook"""
    webhook = WebhookService.get_by_id(db, webhook_id)
    if not webhook or webhook.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 检查权限
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权删除此Webhook")
    
    WebhookService.delete_webhook(db, webhook)
    return None


@workflow_router.post("/{workflow_id}/webhooks/{webhook_id}/regenerate", response_model=WebhookRegenerateResponse)
def regenerate_webhook(
    workflow_id: UUID,
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重新生成Webhook URL和密钥"""
    webhook = WebhookService.get_by_id(db, webhook_id)
    if not webhook or webhook.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 检查权限
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权修改此Webhook")
    
    updated_webhook, webhook_url = WebhookService.regenerate_webhook(db, webhook)
    
    return {
        "uuid": updated_webhook.uuid,
        "webhook_url": webhook_url,
        "secret": updated_webhook.secret
    }


@workflow_router.get("/{workflow_id}/webhooks/{webhook_id}/logs", response_model=WebhookLogListResponse)
def get_webhook_logs(
    workflow_id: UUID,
    webhook_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取Webhook调用日志"""
    webhook = WebhookService.get_by_id(db, webhook_id)
    if not webhook or webhook.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 检查权限
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        workflow = webhook.workflow
        if workflow and workflow.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="无权访问此Webhook")
    
    skip = (page - 1) * page_size
    logs, total = WebhookService.get_logs(db, webhook_id, skip=skip, limit=page_size)
    
    log_list = [WebhookLogResponse.model_validate(log).model_dump() for log in logs]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "data": log_list
    }


# ============ 独立Webhook管理 (不依赖workflow_id) ============

@webhook_router.get("/{webhook_id}", response_model=WebhookDetailResponse)
def get_webhook_by_id(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通过ID获取Webhook详情"""
    webhook = WebhookService.get_by_id(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 检查权限
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        workflow = webhook.workflow
        if workflow and workflow.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="无权访问此Webhook")
    
    response_data = WebhookResponse.model_validate(webhook).model_dump()
    response_data["webhook_url"] = WebhookService.get_webhook_url(webhook.uuid)
    
    return response_data


@webhook_router.put("/{webhook_id}", response_model=WebhookResponse)
def update_webhook_by_id(
    webhook_id: UUID,
    webhook_data: WebhookUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通过ID更新Webhook"""
    webhook = WebhookService.get_by_id(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 检查权限
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权修改此Webhook")
    
    updated_webhook = WebhookService.update_webhook(db, webhook, webhook_data)
    return updated_webhook


@webhook_router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook_by_id(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通过ID删除Webhook"""
    webhook = WebhookService.get_by_id(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 检查权限
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权删除此Webhook")
    
    WebhookService.delete_webhook(db, webhook)
    return None


@webhook_router.post("/{webhook_id}/regenerate", response_model=WebhookRegenerateResponse)
def regenerate_webhook_by_id(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通过ID重新生成Webhook URL和密钥"""
    webhook = WebhookService.get_by_id(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 检查权限
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权修改此Webhook")
    
    updated_webhook, webhook_url = WebhookService.regenerate_webhook(db, webhook)
    
    return {
        "uuid": updated_webhook.uuid,
        "webhook_url": webhook_url,
        "secret": updated_webhook.secret
    }


# ============ 公共Webhook触发端点 (无需认证) ============

@public_router.post("/{webhook_uuid}", response_model=WebhookTriggerResponse)
async def trigger_webhook(
    webhook_uuid: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    公共Webhook触发端点 - 无需认证
    
    通过webhook UUID直接触发工作流执行
    """
    start_time = time.time()
    
    # 获取Webhook
    webhook = WebhookService.get_by_uuid(db, webhook_uuid)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # 获取请求信息
    client_ip = request.client.host if request.client else None
    request_method = request.method
    
    # 获取请求头
    headers = dict(request.headers)
    
    # 获取请求体
    body_bytes = await request.body()
    try:
        request_data = json.loads(body_bytes) if body_bytes else {}
    except json.JSONDecodeError:
        request_data = {"raw_body": body_bytes.decode('utf-8', errors='ignore')}
    
    # 触发工作流
    success, execution_id, error_message = WebhookService.trigger_workflow(
        db=db,
        webhook=webhook,
        request_data=request_data,
        headers=headers,
        client_ip=client_ip,
        request_body=body_bytes
    )
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # 记录日志
    signature = headers.get("x-webhook-signature") or headers.get("x-hub-signature-256")
    signature_valid = None
    if signature and webhook.secret:
        signature_valid = WebhookService.verify_signature(body_bytes, webhook.secret, signature)
    
    WebhookService.create_log(
        db=db,
        webhook_id=webhook.id,
        request_method=request_method,
        request_headers=headers,
        request_body=body_bytes.decode('utf-8', errors='ignore')[:10000],  # 限制日志大小
        request_ip=client_ip,
        response_status=200 if success else 400,
        response_body=json.dumps({"success": success, "execution_id": str(execution_id) if execution_id else None}),
        signature_valid=signature_valid,
        execution_id=execution_id,
        error_message=error_message,
        duration_ms=duration_ms
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error_message)
    
    return {
        "success": True,
        "execution_id": execution_id,
        "message": "Workflow triggered successfully"
    }


@public_router.post("/{webhook_uuid}/trigger")
async def trigger_webhook_simple(
    webhook_uuid: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook触发端点 (简化版，兼容更多格式)
    """
    return await trigger_webhook(webhook_uuid, request, db)


@public_router.get("/{webhook_uuid}")
async def get_webhook_info(
    webhook_uuid: UUID,
    db: Session = Depends(get_db)
):
    """
    获取Webhook基本信息 (用于验证)
    """
    webhook = WebhookService.get_by_uuid(db, webhook_uuid)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    if not webhook.is_active:
        raise HTTPException(status_code=400, detail="Webhook is not active")
    
    return {
        "webhook_id": str(webhook.id),
        "name": webhook.name,
        "is_active": webhook.is_active,
        "workflow_id": str(webhook.workflow_id),
    }


@public_router.head("/{webhook_uuid}")
async def check_webhook(
    webhook_uuid: UUID,
    db: Session = Depends(get_db)
):
    """
    检查Webhook是否可用
    """
    webhook = WebhookService.get_by_uuid(db, webhook_uuid)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    if not webhook.is_active:
        raise HTTPException(status_code=400, detail="Webhook is not active")
    
    return {"status": "ok"}
