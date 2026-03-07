from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
try:
    from sqlalchemy.dialects.postgresql import JSON as JSON
except:
    from sqlalchemy.types import JSON
import uuid

from app.db.base import Base


# 用户-角色关联表
user_role = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE")),
)

# 角色-权限关联表
role_permission = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE")),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE")),
)


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    avatar = Column(String(500))
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # 部门和组织
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    
    # 元数据
    last_login = Column(DateTime)
    preferences = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    roles = relationship("Role", secondary=user_role, back_populates="users")
    department = relationship("Department", back_populates="users")
    tenant = relationship("Tenant", back_populates="users")
    # workflows 和 components 关系在对应模型中定义


class Role(Base):
    """角色模型"""
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    
    # 角色类型: system(系统内置), custom(自定义)
    role_type = Column(String(20), default="custom")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    users = relationship("User", secondary=user_role, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permission, back_populates="roles")


class Permission(Base):
    """权限模型"""
    __tablename__ = "permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(100), unique=True, nullable=False)
    description = Column(String(255))
    
    # 权限类型: menu(菜单), button(按钮), api(API接口), data(数据)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(String(100))
    
    # 权限操作: view, create, update, delete, execute
    action = Column(String(20))
    
    # 父权限
    parent_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"))
    
    # 排序
    sort_order = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    roles = relationship("Role", secondary=role_permission, back_populates="permissions")
    children = relationship("Permission")


class Department(Base):
    """部门模型"""
    __tablename__ = "departments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True)
    description = Column(String(255))
    
    # 层级
    parent_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    level = Column(Integer, default=1)
    path = Column(String(500))  # 存储完整路径，如: /1/2/3/
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    users = relationship("User", back_populates="department")
    parent = relationship("Department", remote_side=[id])


class Tenant(Base):
    """租户模型 - 多租户支持"""
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(500))
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 配置
    settings = Column(JSON, default=dict)
    limits = Column(JSON, default=dict)  # 资源限制
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    users = relationship("User", back_populates="tenant")
