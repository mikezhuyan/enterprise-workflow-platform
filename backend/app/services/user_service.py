from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime

from app.models.user import User, Role, Permission, Department, Tenant
from app.schemas.user import (
    UserCreate, UserUpdate, RoleCreate, RoleUpdate,
    PermissionCreate, DepartmentCreate, DepartmentUpdate,
    TenantCreate, TenantUpdate
)
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token


class UserService:
    """用户服务"""
    
    @staticmethod
    def get_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def list_users(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        department_id: Optional[UUID] = None
    ) -> tuple:
        """获取用户列表"""
        query = db.query(User)
        
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
            )
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if department_id:
            query = query.filter(User.department_id == department_id)
        
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """创建用户"""
        # 检查用户名和邮箱是否已存在
        if UserService.get_by_username(db, user_data.username):
            raise ValueError("用户名已存在")
        if UserService.get_by_email(db, user_data.email):
            raise ValueError("邮箱已存在")
        
        # 创建用户
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            department_id=user_data.department_id
        )
        
        # 添加角色
        if user_data.role_ids:
            roles = db.query(Role).filter(Role.id.in_(user_data.role_ids)).all()
            db_user.roles = roles
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
        """更新用户"""
        update_data = user_data.model_dump(exclude_unset=True)
        
        # 处理角色更新
        if "role_ids" in update_data:
            role_ids = update_data.pop("role_ids")
            if role_ids is not None:
                roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
                user.roles = roles
        
        # 更新其他字段
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def delete_user(db: Session, user: User) -> None:
        """删除用户"""
        db.delete(user)
        db.commit()
    
    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = UserService.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> bool:
        """修改密码"""
        if not verify_password(old_password, user.hashed_password):
            return False
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        return True


class RoleService:
    """角色服务"""
    
    @staticmethod
    def get_by_id(db: Session, role_id: UUID) -> Optional[Role]:
        return db.query(Role).filter(Role.id == role_id).first()
    
    @staticmethod
    def list_roles(db: Session, skip: int = 0, limit: int = 100) -> tuple:
        query = db.query(Role)
        total = query.count()
        roles = query.offset(skip).limit(limit).all()
        return roles, total
    
    @staticmethod
    def create_role(db: Session, role_data: RoleCreate) -> Role:
        db_role = Role(
            name=role_data.name,
            description=role_data.description,
            role_type=role_data.role_type
        )
        
        if role_data.permission_ids:
            permissions = db.query(Permission).filter(
                Permission.id.in_(role_data.permission_ids)
            ).all()
            db_role.permissions = permissions
        
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        return db_role
    
    @staticmethod
    def update_role(db: Session, role: Role, role_data: RoleUpdate) -> Role:
        update_data = role_data.model_dump(exclude_unset=True)
        
        if "permission_ids" in update_data:
            permission_ids = update_data.pop("permission_ids")
            if permission_ids is not None:
                permissions = db.query(Permission).filter(
                    Permission.id.in_(permission_ids)
                ).all()
                role.permissions = permissions
        
        for field, value in update_data.items():
            setattr(role, field, value)
        
        role.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(role)
        return role
    
    @staticmethod
    def delete_role(db: Session, role: Role) -> None:
        db.delete(role)
        db.commit()


class PermissionService:
    """权限服务"""
    
    @staticmethod
    def get_by_id(db: Session, permission_id: UUID) -> Optional[Permission]:
        return db.query(Permission).filter(Permission.id == permission_id).first()
    
    @staticmethod
    def list_permissions(
        db: Session,
        resource_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple:
        query = db.query(Permission)
        if resource_type:
            query = query.filter(Permission.resource_type == resource_type)
        
        total = query.count()
        permissions = query.offset(skip).limit(limit).all()
        return permissions, total
    
    @staticmethod
    def create_permission(db: Session, perm_data: PermissionCreate) -> Permission:
        db_perm = Permission(**perm_data.model_dump())
        db.add(db_perm)
        db.commit()
        db.refresh(db_perm)
        return db_perm
    
    @staticmethod
    def get_permission_tree(db: Session) -> list:
        """获取权限树"""
        permissions = db.query(Permission).order_by(Permission.sort_order).all()
        
        # 构建树形结构
        perm_dict = {}
        for perm in permissions:
            perm_dict[perm.id] = {
                "id": perm.id,
                "name": perm.name,
                "code": perm.code,
                "resource_type": perm.resource_type,
                "action": perm.action,
                "children": []
            }
        
        tree = []
        for perm in permissions:
            if perm.parent_id is None:
                tree.append(perm_dict[perm.id])
            elif perm.parent_id in perm_dict:
                perm_dict[perm.parent_id]["children"].append(perm_dict[perm.id])
        
        return tree


class DepartmentService:
    """部门服务"""
    
    @staticmethod
    def get_by_id(db: Session, dept_id: UUID) -> Optional[Department]:
        return db.query(Department).filter(Department.id == dept_id).first()
    
    @staticmethod
    def list_departments(db: Session) -> list:
        return db.query(Department).order_by(Department.sort_order).all()
    
    @staticmethod
    def create_department(db: Session, dept_data: DepartmentCreate) -> Department:
        dept = Department(**dept_data.model_dump())
        
        # 计算层级和路径
        if dept.parent_id:
            parent = DepartmentService.get_by_id(db, dept.parent_id)
            if parent:
                dept.level = parent.level + 1
                dept.path = f"{parent.path}{dept.id}/"
        else:
            dept.level = 1
            dept.path = f"/{dept.id}/"
        
        db.add(dept)
        db.commit()
        db.refresh(dept)
        return dept
    
    @staticmethod
    def get_department_tree(db: Session) -> list:
        """获取部门树"""
        departments = db.query(Department).order_by(Department.sort_order).all()
        
        dept_dict = {}
        for dept in departments:
            dept_dict[dept.id] = {
                "id": dept.id,
                "name": dept.name,
                "code": dept.code,
                "children": []
            }
        
        tree = []
        for dept in departments:
            if dept.parent_id is None:
                tree.append(dept_dict[dept.id])
            elif dept.parent_id in dept_dict:
                dept_dict[dept.parent_id]["children"].append(dept_dict[dept.id])
        
        return tree


class TenantService:
    """租户服务"""
    
    @staticmethod
    def get_by_id(db: Session, tenant_id: UUID) -> Optional[Tenant]:
        return db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Tenant]:
        return db.query(Tenant).filter(Tenant.code == code).first()
    
    @staticmethod
    def list_tenants(db: Session, skip: int = 0, limit: int = 100) -> tuple:
        query = db.query(Tenant)
        total = query.count()
        tenants = query.offset(skip).limit(limit).all()
        return tenants, total
    
    @staticmethod
    def create_tenant(db: Session, tenant_data: TenantCreate) -> Tenant:
        if TenantService.get_by_code(db, tenant_data.code):
            raise ValueError("租户编码已存在")
        
        tenant = Tenant(
            name=tenant_data.name,
            code=tenant_data.code,
            description=tenant_data.description,
            settings=tenant_data.settings,
            limits=tenant_data.limits
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant
    
    @staticmethod
    def update_tenant(db: Session, tenant: Tenant, tenant_data: TenantUpdate) -> Tenant:
        update_data = tenant_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)
        
        tenant.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(tenant)
        return tenant
