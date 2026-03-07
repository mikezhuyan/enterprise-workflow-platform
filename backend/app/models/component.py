from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
try:
    from sqlalchemy.dialects.postgresql import JSON as JSON
except:
    from sqlalchemy.types import JSON
import uuid
import enum

from app.db.base import Base


class ComponentType(str, enum.Enum):
    """组件类型"""
    API = "api"               # HTTP API调用
    DATABASE = "database"     # 数据库操作
    MESSAGE = "message"       # 消息队列
    SCRIPT = "script"         # 脚本执行
    AI = "ai"                 # AI/LLM组件
    CONDITION = "condition"   # 条件判断
    LOOP = "loop"             # 循环
    DELAY = "delay"           # 延时
    SUBFLOW = "subflow"       # 子工作流
    CUSTOM = "custom"         # 自定义组件
    MCP = "mcp"               # MCP组件
    AGENT = "agent"           # Agent组件


class ComponentStatus(str, enum.Enum):
    """组件状态"""
    DEVELOPMENT = "development"  # 开发中
    TESTING = "testing"          # 测试中
    PUBLISHED = "published"      # 已发布
    DEPRECATED = "deprecated"    # 已废弃


class ProtocolType(str, enum.Enum):
    """协议类型"""
    HTTP = "http"
    HTTPS = "https"
    GRPC = "grpc"
    WEBSOCKET = "websocket"
    MQTT = "mqtt"
    KAFKA = "kafka"
    RABBITMQ = "rabbitmq"
    SOAP = "soap"
    GRAPHQL = "graphql"


class Component(Base):
    """组件模型 - 可复用的功能单元"""
    __tablename__ = "components"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(1000))
    
    # 组件类型
    component_type = Column(String(30), nullable=False)
    
    # 版本
    version = Column(String(20), default="1.0.0")
    
    # 状态
    status = Column(String(20), default=ComponentStatus.DEVELOPMENT.value)
    
    # 图标和分类
    icon = Column(String(200))
    color = Column(String(20))
    category_id = Column(UUID(as_uuid=True), ForeignKey("component_categories.id"))
    tags = Column(JSON, default=list)
    
    # 组件定义
    # schema 定义输入参数
    input_schema = Column(JSON, default=dict)  # { properties: {}, required: [] }
    # schema 定义输出结果
    output_schema = Column(JSON, default=dict)
    # 组件配置
    config_schema = Column(JSON, default=dict)  # UI配置表单
    
    # 执行逻辑
    # 对于传统组件: 存储协议配置
    # 对于AI组件: 存储prompt/技能配置
    # 对于MCP组件: 存储MCP服务器配置
    execution_config = Column(JSON, default=dict)
    
    # 代码实现 (可选，用于自定义组件)
    implementation = Column(Text)
    language = Column(String(20))  # python, javascript, etc.
    
    # 文档
    documentation = Column(Text)
    examples = Column(JSON, default=list)
    
    # 统计
    usage_count = Column(Integer, default=0)
    rating = Column(Integer, default=5)
    
    # 权限
    visibility = Column(String(20), default="private")  # private, tenant, public
    allowed_tenants = Column(JSON, default=list)
    
    # 所有者
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    
    # 审核
    is_approved = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    
    # 关联
    creator = relationship("User", foreign_keys=[created_by])
    category = relationship("ComponentCategory", back_populates="components")
    versions = relationship("ComponentVersion", back_populates="component")


class ComponentVersion(Base):
    """组件版本"""
    __tablename__ = "component_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component_id = Column(UUID(as_uuid=True), ForeignKey("components.id"), nullable=False)
    version = Column(String(20), nullable=False)
    
    # 变更说明
    changelog = Column(Text)
    
    # 版本定义 (复制component的数据)
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    execution_config = Column(JSON)
    implementation = Column(Text)
    
    # 是否是当前版本
    is_current = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # 关联
    component = relationship("Component", back_populates="versions")


class ComponentCategory(Base):
    """组件分类"""
    __tablename__ = "component_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(500))
    icon = Column(String(100))
    
    # 分类类型: system(系统内置), custom(自定义)
    category_type = Column(String(20), default="custom")
    
    # 排序
    sort_order = Column(Integer, default=0)
    
    # 父分类
    parent_id = Column(UUID(as_uuid=True), ForeignKey("component_categories.id"))
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    components = relationship("Component", back_populates="category")
    parent = relationship("ComponentCategory", remote_side=[id])


class APIDefinition(Base):
    """API定义 - 用于API类型组件"""
    __tablename__ = "api_definitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component_id = Column(UUID(as_uuid=True), ForeignKey("components.id"), nullable=False)
    
    # 协议
    protocol = Column(String(20), default=ProtocolType.HTTP.value)
    
    # 基础URL
    base_url = Column(String(500))
    
    # 路径
    path = Column(String(500))
    method = Column(String(10))  # GET, POST, PUT, DELETE, etc.
    
    # 请求配置
    headers = Column(JSON, default=dict)
    query_params = Column(JSON, default=dict)
    body_template = Column(Text)
    
    # 认证
    auth_type = Column(String(20))  # none, basic, bearer, apikey, oauth2
    auth_config = Column(JSON, default=dict)
    
    # 响应处理
    response_mapping = Column(JSON, default=dict)  # 字段映射
    error_mapping = Column(JSON, default=dict)
    
    # 超时和重试
    timeout = Column(Integer, default=30)
    retry_count = Column(Integer, default=0)
    retry_interval = Column(Integer, default=1)
    
    # SSL配置
    verify_ssl = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MCPServer(Base):
    """MCP服务器配置"""
    __tablename__ = "mcp_servers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))
    
    # 服务器配置
    transport_type = Column(String(20), default="stdio")  # stdio, http
    command = Column(String(200))  # 用于stdio: python, node等
    args = Column(JSON, default=list)  # 参数
    env = Column(JSON, default=dict)  # 环境变量
    
    # HTTP配置
    url = Column(String(500))
    headers = Column(JSON, default=dict)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))


class AgentSkill(Base):
    """Agent技能定义"""
    __tablename__ = "agent_skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))
    
    # 技能定义
    definition = Column(JSON, default=dict)
    # {
    #   "system_prompt": "...",
    #   "tools": [...],
    #   "memory_config": {...},
    #   "model_config": {...}
    # }
    
    # 关联组件
    component_id = Column(UUID(as_uuid=True), ForeignKey("components.id"))
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
