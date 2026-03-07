from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID


# ============ 基础Schema ============

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ============ 权限Schema ============

class PermissionBase(BaseSchema):
    name: str
    code: str
    description: Optional[str] = None
    resource_type: str
    resource_id: Optional[str] = None
    action: Optional[str] = None
    sort_order: int = 0


class PermissionCreate(PermissionBase):
    parent_id: Optional[UUID] = None


class PermissionUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class PermissionResponse(PermissionBase):
    id: UUID
    parent_id: Optional[UUID] = None
    created_at: datetime


# ============ 角色Schema ============

class RoleBase(BaseSchema):
    name: str
    description: Optional[str] = None
    role_type: str = "custom"


class RoleCreate(RoleBase):
    permission_ids: List[UUID] = []


class RoleUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[UUID]] = None


class RoleResponse(RoleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionResponse] = []


class RoleListResponse(BaseSchema):
    id: UUID
    name: str
    description: Optional[str]
    role_type: str


# ============ 用户Schema ============

class UserBase(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role_ids: List[UUID] = []
    department_id: Optional[UUID] = None


class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    is_active: Optional[bool] = None
    role_ids: Optional[List[UUID]] = None
    department_id: Optional[UUID] = None


class UserResponse(UserBase):
    id: UUID
    avatar: Optional[str]
    is_active: bool
    is_superuser: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    roles: List[RoleListResponse] = []


class UserDetailResponse(UserResponse):
    department: Optional[dict] = None
    preferences: dict = {}


# ============ 认证Schema ============

class LoginRequest(BaseSchema):
    username: str
    password: str


class LoginResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class ChangePasswordRequest(BaseSchema):
    old_password: str
    new_password: str = Field(..., min_length=6)


class ResetPasswordRequest(BaseSchema):
    email: EmailStr


# ============ 部门Schema ============

class DepartmentBase(BaseSchema):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None


class DepartmentResponse(DepartmentBase):
    id: UUID
    level: int
    path: Optional[str]
    created_at: datetime
    children: List["DepartmentResponse"] = []


# ============ 租户Schema ============

class TenantBase(BaseSchema):
    name: str
    code: str
    description: Optional[str] = None


class TenantCreate(TenantBase):
    settings: dict = {}
    limits: dict = {}


class TenantUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[dict] = None
    limits: Optional[dict] = None


class TenantResponse(TenantBase):
    id: UUID
    is_active: bool
    settings: dict
    limits: dict
    created_at: datetime
    updated_at: datetime


# ============ 分页Schema ============

class PaginationParams(BaseSchema):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseSchema):
    total: int
    page: int
    page_size: int
    pages: int
    data: List[Any] = []
