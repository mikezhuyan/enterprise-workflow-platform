from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.core.security import get_current_user, get_current_superuser, PermissionChecker
from app.services.user_service import UserService, RoleService, PermissionService, DepartmentService
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserDetailResponse,
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionResponse, DepartmentCreate, DepartmentResponse,
    PaginatedResponse
)
from app.models.user import User

router = APIRouter()


# ============ 角色管理 (放在用户路由之前) ============

@router.get("/roles", response_model=PaginatedResponse)
def list_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取角色列表"""
    skip = (page - 1) * page_size
    roles, total = RoleService.list_roles(db, skip=skip, limit=page_size)
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "data": roles
    }


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """创建角色 (仅超级管理员)"""
    return RoleService.create_role(db, role_data)


@router.get("/roles/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取角色详情"""
    role = RoleService.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return role


@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """更新角色 (仅超级管理员)"""
    role = RoleService.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return RoleService.update_role(db, role, role_data)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """删除角色 (仅超级管理员)"""
    role = RoleService.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    RoleService.delete_role(db, role)
    return None


# ============ 权限管理 ============

@router.get("/permissions/tree")
def get_permission_tree(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取权限树"""
    return PermissionService.get_permission_tree(db)


@router.get("/permissions", response_model=List[PermissionResponse])
def list_permissions(
    resource_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取权限列表"""
    permissions, _ = PermissionService.list_permissions(db, resource_type=resource_type)
    return permissions


# ============ 部门管理 ============

@router.get("/departments/tree")
def get_department_tree(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取部门树"""
    return DepartmentService.get_department_tree(db)


@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取部门列表"""
    return DepartmentService.list_departments(db)


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    dept_data: DepartmentCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """创建部门 (仅超级管理员)"""
    return DepartmentService.create_department(db, dept_data)


# ============ 用户管理 (放在最后，避免动态路由冲突) ============

@router.get("", response_model=PaginatedResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    department_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    skip = (page - 1) * page_size
    users, total = UserService.list_users(
        db, skip=skip, limit=page_size,
        search=search, is_active=is_active,
        department_id=department_id
    )
    
    # 将SQLAlchemy对象转换为Pydantic模型
    user_list = [UserResponse.model_validate(u).model_dump() for u in users]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "data": user_list
    }


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """创建用户 (仅超级管理员)"""
    try:
        return UserService.create_user(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户详情"""
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户"""
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 普通用户只能更新自己
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="权限不足")
    
    return UserService.update_user(db, user, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """删除用户 (仅超级管理员)"""
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    UserService.delete_user(db, user)
    return None
