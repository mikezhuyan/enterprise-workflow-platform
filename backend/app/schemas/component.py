from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from app.models.component import ComponentType, ComponentStatus


# ============ 基础Schema ============

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ============ Schema定义 ============

class PropertySchema(BaseSchema):
    """属性Schema定义"""
    type: str  # string, number, boolean, object, array
    title: Optional[str] = None
    description: Optional[str] = None
    default: Any = None
    enum: Optional[List[Any]] = None
    format: Optional[str] = None  # date-time, email, uri, etc.


class ComponentSchema(BaseSchema):
    """组件输入/输出Schema"""
    type: str = "object"
    properties: Dict[str, PropertySchema] = Field(default_factory=dict)
    required: List[str] = []


# ============ 组件Schema ============

class ComponentBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    component_type: str
    icon: Optional[str] = None
    color: Optional[str] = None


class ComponentCreate(ComponentBase):
    category_id: Optional[UUID] = None
    tags: List[str] = []
    
    # Schema定义
    input_schema: ComponentSchema = Field(default_factory=ComponentSchema)
    output_schema: ComponentSchema = Field(default_factory=ComponentSchema)
    config_schema: ComponentSchema = Field(default_factory=ComponentSchema)
    
    # 执行配置
    execution_config: Dict[str, Any] = Field(default_factory=dict)
    
    # 代码实现（自定义组件）
    implementation: Optional[str] = None
    language: Optional[str] = None
    
    # 文档
    documentation: Optional[str] = None
    examples: List[Dict[str, Any]] = []
    
    # 可见性
    visibility: str = "private"


class ComponentUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    
    input_schema: Optional[ComponentSchema] = None
    output_schema: Optional[ComponentSchema] = None
    config_schema: Optional[ComponentSchema] = None
    execution_config: Optional[Dict[str, Any]] = None
    
    implementation: Optional[str] = None
    language: Optional[str] = None
    documentation: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None
    visibility: Optional[str] = None


class ComponentResponse(ComponentBase):
    id: UUID
    version: str
    status: str
    
    category_id: Optional[UUID]
    tags: List[str]
    
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    config_schema: Dict[str, Any]
    execution_config: Dict[str, Any]
    
    implementation: Optional[str]
    language: Optional[str]
    
    documentation: Optional[str]
    examples: List[Dict[str, Any]]
    
    usage_count: int
    rating: int
    visibility: str
    
    created_by: UUID
    tenant_id: Optional[UUID]
    is_approved: bool
    
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]


class ComponentListResponse(ComponentBase):
    """组件列表响应"""
    id: UUID
    version: str
    status: str
    category_id: Optional[UUID]
    tags: List[str]
    usage_count: int
    rating: int
    visibility: str
    created_by: UUID
    created_at: datetime


class ComponentDetailResponse(ComponentResponse):
    """组件详情响应"""
    creator: Optional[Dict[str, Any]] = None
    category: Optional[Dict[str, Any]] = None


# ============ 组件版本Schema ============

class ComponentVersionResponse(BaseSchema):
    id: UUID
    component_id: UUID
    version: str
    changelog: Optional[str]
    is_current: bool
    created_at: datetime
    created_by: Optional[UUID]


class ComponentVersionCreate(BaseSchema):
    version: str
    changelog: Optional[str] = None


# ============ 组件分类Schema ============

class ComponentCategoryBase(BaseSchema):
    name: str
    code: str
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[UUID] = None


class ComponentCategoryCreate(ComponentCategoryBase):
    category_type: str = "custom"
    sort_order: int = 0


class ComponentCategoryUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    parent_id: Optional[UUID] = None


class ComponentCategoryResponse(ComponentCategoryBase):
    id: UUID
    category_type: str
    sort_order: int
    created_at: datetime
    children: List["ComponentCategoryResponse"] = []


# ============ API定义Schema ============

class APIDefinitionBase(BaseSchema):
    """API组件定义"""
    component_id: UUID
    protocol: str = "http"
    base_url: str
    path: str
    method: str = "GET"
    
    headers: Dict[str, str] = Field(default_factory=dict)
    query_params: Dict[str, str] = Field(default_factory=dict)
    body_template: Optional[str] = None
    
    auth_type: str = "none"
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    
    response_mapping: Dict[str, Any] = Field(default_factory=dict)
    error_mapping: Dict[str, Any] = Field(default_factory=dict)
    
    timeout: int = 30
    retry_count: int = 0
    retry_interval: int = 1
    verify_ssl: bool = True


class APIDefinitionCreate(APIDefinitionBase):
    pass


class APIDefinitionUpdate(BaseSchema):
    protocol: Optional[str] = None
    base_url: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, str]] = None
    body_template: Optional[str] = None
    auth_type: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    response_mapping: Optional[Dict[str, Any]] = None
    error_mapping: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    retry_count: Optional[int] = None


class APIDefinitionResponse(APIDefinitionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


# ============ MCP服务器Schema ============

class MCPServerBase(BaseSchema):
    name: str
    code: str
    description: Optional[str] = None
    transport_type: str = "stdio"
    
    # stdio配置
    command: Optional[str] = None
    args: List[str] = []
    env: Dict[str, str] = Field(default_factory=dict)
    
    # http配置
    url: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    
    is_active: bool = True


class MCPServerCreate(MCPServerBase):
    pass


class MCPServerUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    transport_type: Optional[str] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class MCPServerResponse(MCPServerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID


# ============ Agent技能Schema ============

class AgentSkillBase(BaseSchema):
    name: str
    code: str
    description: Optional[str] = None
    definition: Dict[str, Any] = Field(default_factory=dict)
    component_id: Optional[UUID] = None
    is_active: bool = True


class AgentSkillCreate(AgentSkillBase):
    pass


class AgentSkillUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None
    component_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class AgentSkillResponse(AgentSkillBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID


# ============ 组件测试Schema ============

class ComponentTestRequest(BaseSchema):
    """组件测试请求"""
    input_data: Dict[str, Any] = Field(default_factory=dict)
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    test_mode: bool = True


class ComponentTestResponse(BaseSchema):
    """组件测试响应"""
    success: bool
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_detail: Optional[Dict[str, Any]] = None
    duration_ms: int
    logs: List[str] = []
