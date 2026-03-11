"""
Webhook Schema定义
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ============ Webhook Schema ============

class WebhookBase(BaseSchema):
    """Webhook基础Schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class WebhookCreate(WebhookBase):
    """创建Webhook请求"""
    require_signature: bool = False
    rate_limit: int = Field(0, ge=0)  # 0表示不限制


class WebhookUpdate(BaseSchema):
    """更新Webhook请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    require_signature: Optional[bool] = None
    rate_limit: Optional[int] = Field(None, ge=0)


class WebhookResponse(WebhookBase):
    """Webhook响应"""
    id: UUID
    workflow_id: UUID
    uuid: UUID
    secret: Optional[str]  # 仅创建时返回
    require_signature: bool
    is_active: bool
    rate_limit: int
    call_count: int
    last_called_at: Optional[datetime]
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class WebhookListResponse(WebhookBase):
    """Webhook列表响应"""
    id: UUID
    workflow_id: UUID
    uuid: UUID
    is_active: bool
    call_count: int
    last_called_at: Optional[datetime]
    created_at: datetime


class WebhookDetailResponse(WebhookResponse):
    """Webhook详情响应 (包含URL)"""
    webhook_url: str


class WebhookRegenerateResponse(BaseSchema):
    """重新生成Webhook URL响应"""
    uuid: UUID
    webhook_url: str
    secret: Optional[str]


# ============ Webhook日志 Schema ============

class WebhookLogResponse(BaseSchema):
    """Webhook日志响应"""
    id: UUID
    webhook_id: UUID
    request_method: Optional[str]
    request_headers: Optional[Dict[str, Any]]
    request_body: Optional[str]
    request_ip: Optional[str]
    response_status: Optional[int]
    response_body: Optional[str]
    signature_valid: Optional[bool]
    execution_id: Optional[UUID]
    error_message: Optional[str]
    duration_ms: Optional[int]
    created_at: datetime


class WebhookLogListResponse(BaseSchema):
    """Webhook日志列表响应"""
    total: int
    page: int
    page_size: int
    pages: int
    data: List[WebhookLogResponse]


# ============ Webhook触发 Schema ============

class WebhookTriggerResponse(BaseSchema):
    """Webhook触发响应"""
    success: bool
    execution_id: Optional[UUID]
    message: str
