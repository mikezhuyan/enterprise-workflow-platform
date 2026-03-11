from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from app.models.workflow import WorkflowStatus, ExecutionStatus


# ============ 基础Schema ============

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ============ 工作流节点Schema ============

class WorkflowNode(BaseSchema):
    """工作流节点定义"""
    id: str
    type: str
    position: Dict[str, float] = Field(default_factory=dict)  # {x, y}
    data: Dict[str, Any] = Field(default_factory=dict)  # 节点配置
    width: Optional[float] = None
    height: Optional[float] = None
    selected: bool = False


class WorkflowEdge(BaseSchema):
    """工作流连接定义"""
    id: str
    source: str
    target: str
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None
    type: Optional[str] = None
    label: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    animated: bool = False


class WorkflowDefinition(BaseSchema):
    """工作流定义结构"""
    nodes: List[WorkflowNode] = []
    edges: List[WorkflowEdge] = []
    viewport: Optional[Dict[str, Any]] = None


# ============ 变量Schema ============

class WorkflowVariable(BaseSchema):
    """工作流变量定义"""
    name: str
    type: str  # string, number, boolean, object, array, datetime
    default: Any = None
    required: bool = False
    description: Optional[str] = None


# ============ 触发器Schema ============

class WorkflowTrigger(BaseSchema):
    """工作流触发器配置"""
    type: str  # manual, webhook, schedule, event, api
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


# ============ 工作流Schema ============

class WorkflowBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class WorkflowCreate(WorkflowBase):
    category_id: Optional[UUID] = None
    definition: WorkflowDefinition = Field(default_factory=WorkflowDefinition)
    variables: List[WorkflowVariable] = []
    triggers: List[WorkflowTrigger] = []
    tags: List[str] = []
    is_template: bool = False


class WorkflowUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    definition: Optional[WorkflowDefinition] = None
    variables: Optional[List[WorkflowVariable]] = None
    triggers: Optional[List[WorkflowTrigger]] = None
    tags: Optional[List[str]] = None


class WorkflowResponse(WorkflowBase):
    id: UUID
    version: str
    status: str
    is_template: bool
    definition: Dict[str, Any]
    variables: List[Dict[str, Any]]
    triggers: List[Dict[str, Any]]
    tags: List[str]
    category_id: Optional[UUID]
    execution_count: int
    success_count: int
    fail_count: int
    created_by: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]


class WorkflowListResponse(WorkflowBase):
    """工作流列表响应"""
    id: UUID
    version: str
    status: str
    is_template: bool
    category_id: Optional[UUID]
    execution_count: int
    created_by: UUID
    created_at: datetime


class WorkflowPublishRequest(BaseSchema):
    version: Optional[str] = None  # 不传则自动递增
    comment: Optional[str] = None


class WorkflowExecuteRequest(BaseSchema):
    input_data: Dict[str, Any] = Field(default_factory=dict)
    synchronous: bool = True  # 是否同步执行
    timeout: Optional[int] = None


# ============ 执行记录Schema ============

class WorkflowExecutionResponse(BaseSchema):
    id: UUID
    workflow_id: UUID
    status: str
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    context: Dict[str, Any]
    error_message: Optional[str]
    error_detail: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    triggered_by: Optional[UUID]
    trigger_type: Optional[str]
    created_at: datetime


class NodeExecutionResponse(BaseSchema):
    id: UUID
    execution_id: UUID
    node_id: str
    node_type: str
    node_name: Optional[str]
    status: str
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    retry_count: int
    created_at: datetime


class ExecutionLogResponse(BaseSchema):
    id: UUID
    execution_id: Optional[UUID]
    node_execution_id: Optional[UUID]
    level: str
    message: str
    data: Optional[Dict[str, Any]]
    created_at: datetime


class ExecutionDetailResponse(WorkflowExecutionResponse):
    node_executions: List[NodeExecutionResponse] = []


# ============ 工作流分类Schema ============

class WorkflowCategoryBase(BaseSchema):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[UUID] = None


class WorkflowCategoryCreate(WorkflowCategoryBase):
    sort_order: int = 0


class WorkflowCategoryUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
    parent_id: Optional[UUID] = None


class WorkflowCategoryResponse(WorkflowCategoryBase):
    id: UUID
    sort_order: int
    created_at: datetime
    children: List["WorkflowCategoryResponse"] = []


# ============ 定时任务Schema ============

class WorkflowScheduleBase(BaseSchema):
    workflow_id: UUID
    cron_expression: str
    timezone: str = "UTC"
    input_data: Dict[str, Any] = Field(default_factory=dict)


class WorkflowScheduleCreate(WorkflowScheduleBase):
    pass


class WorkflowScheduleUpdate(BaseSchema):
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    input_data: Optional[Dict[str, Any]] = None


class WorkflowScheduleResponse(WorkflowScheduleBase):
    id: UUID
    is_active: bool
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ============ 统计Schema ============

class WorkflowStatsResponse(BaseSchema):
    total_workflows: int
    active_workflows: int
    total_executions: int
    success_rate: float
    avg_duration_ms: int
    executions_today: int
    executions_this_week: int
    executions_this_month: int


# ============ 版本控制Schema ============

class WorkflowVersionCreate(BaseSchema):
    """创建工作流版本请求"""
    version_type: str = "minor"  # major, minor, patch
    comment: Optional[str] = None


class WorkflowVersionResponse(BaseSchema):
    """工作流版本响应"""
    id: UUID
    name: str
    version: str
    status: str
    description: Optional[str]
    created_by: UUID
    created_at: datetime
    parent_id: Optional[UUID]
    comment: Optional[str] = None  # 版本说明


class WorkflowVersionListResponse(BaseSchema):
    """版本列表响应"""
    versions: List[WorkflowVersionResponse]
    total: int


class WorkflowRollbackRequest(BaseSchema):
    """回滚请求"""
    comment: Optional[str] = None


class WorkflowRollbackResponse(BaseSchema):
    """回滚响应"""
    message: str
    new_version: str
    workflow_id: UUID


class WorkflowVersionCompareRequest(BaseSchema):
    """版本比较请求"""
    version1: str  # 基准版本
    version2: str  # 对比版本


class WorkflowVersionChange(BaseSchema):
    """版本变更详情"""
    field: str
    type: str  # added, removed, modified
    old: Optional[Any] = None
    new: Optional[Any] = None
    added: Optional[List[str]] = None
    removed: Optional[List[str]] = None
    node_changes: Optional[List[Dict[str, Any]]] = None
    edge_changes: Optional[List[Dict[str, Any]]] = None


class WorkflowVersionCompareSummary(BaseSchema):
    """版本比较摘要"""
    total_changes: int
    nodes_added: int
    nodes_removed: int
    nodes_modified: int
    edges_added: int
    edges_removed: int


class WorkflowVersionCompareResponse(BaseSchema):
    """版本比较响应"""
    version1: str
    version2: str
    workflow_id: UUID
    changes: List[WorkflowVersionChange]
    summary: WorkflowVersionCompareSummary
    diff_text: Optional[str] = None


# ============ 审批任务Schema ============

class ApprovalTaskStatus(str, Enum):
    """审批任务状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TRANSFERRED = "transferred"


class ApprovalTaskBase(BaseSchema):
    """审批任务基础Schema"""
    node_id: str
    node_name: Optional[str] = None
    assignee_type: str = "user"  # user, role, department
    assignee_id: UUID
    timeout_seconds: int = 86400
    auto_action: str = "reject"


class ApprovalTaskCreate(ApprovalTaskBase):
    """创建审批任务"""
    execution_id: UUID
    input_data: Dict[str, Any] = Field(default_factory=dict)


class ApprovalTaskResponse(ApprovalTaskBase):
    """审批任务响应"""
    id: UUID
    execution_id: UUID
    status: str  # pending, approved, rejected, transferred
    comment: Optional[str] = None
    transferred_from: Optional[UUID] = None
    transferred_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completed_by: Optional[UUID] = None
    timeout_at: Optional[datetime] = None
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ApprovalTaskListResponse(BaseSchema):
    """审批任务列表响应"""
    id: UUID
    execution_id: UUID
    node_id: str
    node_name: Optional[str] = None
    status: str
    assignee_type: str
    assignee_id: UUID
    completed_by: Optional[UUID] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class ApprovalActionRequest(BaseSchema):
    """审批操作请求"""
    comment: Optional[str] = None


class ApprovalTransferRequest(BaseSchema):
    """转办请求"""
    new_assignee_id: UUID
    comment: Optional[str] = None


class ApprovalActionResponse(BaseSchema):
    """审批操作响应"""
    success: bool
    message: str
    task_id: UUID
    status: str
    completed_at: datetime
