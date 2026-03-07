from datetime import datetime
from typing import List, Optional, Dict, Any
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
