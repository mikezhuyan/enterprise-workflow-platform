from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
try:
    from sqlalchemy.dialects.postgresql import JSON as JSON
except:
    from sqlalchemy.types import JSON
import uuid
import enum

from app.db.base import Base


class WorkflowStatus(str, enum.Enum):
    """工作流状态"""
    DRAFT = "draft"           # 草稿
    PUBLISHED = "published"   # 已发布
    ARCHIVED = "archived"     # 已归档
    DISABLED = "disabled"     # 已禁用


class ExecutionStatus(str, enum.Enum):
    """执行状态"""
    PENDING = "pending"       # 待执行
    RUNNING = "running"       # 执行中
    SUCCESS = "success"       # 成功
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消
    TIMEOUT = "timeout"       # 超时


class Workflow(Base):
    """工作流定义模型"""
    __tablename__ = "workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # 版本控制
    version = Column(String(20), default="1.0.0")
    parent_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"))
    
    # 状态
    status = Column(String(20), default=WorkflowStatus.DRAFT.value)
    is_template = Column(Boolean, default=False)
    
    # 工作流定义 (节点和连接)
    definition = Column(JSON, default=dict)  # { nodes: [], edges: [], config: {} }
    
    # 变量定义
    variables = Column(JSON, default=list)  # [{ name, type, default, required }]
    
    # 触发配置
    triggers = Column(JSON, default=list)  # [{ type, config }]
    
    # 分类和标签
    category_id = Column(UUID(as_uuid=True), ForeignKey("workflow_categories.id"))
    tags = Column(JSON, default=list)
    
    # 统计
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    
    # 所有者
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    
    # 关联
    creator = relationship("User")
    category = relationship("WorkflowCategory", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow")


class WorkflowExecution(Base):
    """工作流执行记录"""
    __tablename__ = "workflow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    
    # 执行状态
    status = Column(String(20), default=ExecutionStatus.PENDING.value)
    
    # 输入输出
    input_data = Column(JSON)
    output_data = Column(JSON)
    
    # 执行上下文
    context = Column(JSON, default=dict)  # 执行过程中的上下文数据
    
    # 错误信息
    error_message = Column(Text)
    error_detail = Column(JSON)
    
    # 执行时间
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)  # 执行时长(毫秒)
    
    # 执行者
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    trigger_type = Column(String(50))  # manual, webhook, schedule, api
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    workflow = relationship("Workflow", back_populates="executions")
    node_executions = relationship("NodeExecution", back_populates="execution")


class NodeExecution(Base):
    """节点执行记录"""
    __tablename__ = "node_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id"), nullable=False)
    
    # 节点信息
    node_id = Column(String(100), nullable=False)  # 工作流定义中的节点ID
    node_type = Column(String(50), nullable=False)
    node_name = Column(String(100))
    
    # 执行状态
    status = Column(String(20), default=ExecutionStatus.PENDING.value)
    
    # 输入输出
    input_data = Column(JSON)
    output_data = Column(JSON)
    
    # 错误信息
    error_message = Column(Text)
    
    # 执行时间
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)
    
    # 重试信息
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    execution = relationship("WorkflowExecution", back_populates="node_executions")
    logs = relationship("ExecutionLog", back_populates="node_execution")


class ExecutionLog(Base):
    """执行日志"""
    __tablename__ = "execution_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id"))
    node_execution_id = Column(UUID(as_uuid=True), ForeignKey("node_executions.id"))
    
    # 日志级别
    level = Column(String(20), default="info")  # debug, info, warning, error
    
    # 日志内容
    message = Column(Text, nullable=False)
    data = Column(JSON)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    node_execution = relationship("NodeExecution", back_populates="logs")


class WorkflowCategory(Base):
    """工作流分类"""
    __tablename__ = "workflow_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    icon = Column(String(100))
    color = Column(String(20))
    
    # 排序
    sort_order = Column(Integer, default=0)
    
    # 父分类
    parent_id = Column(UUID(as_uuid=True), ForeignKey("workflow_categories.id"))
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    workflows = relationship("Workflow", back_populates="category")
    parent = relationship("WorkflowCategory", remote_side=[id])


class WorkflowSchedule(Base):
    """工作流定时任务"""
    __tablename__ = "workflow_schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    
    # 定时规则
    cron_expression = Column(String(100))  # Cron表达式
    timezone = Column(String(50), default="UTC")
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 执行参数
    input_data = Column(JSON, default=dict)
    
    # 下次执行时间
    next_run_at = Column(DateTime)
    last_run_at = Column(DateTime)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
