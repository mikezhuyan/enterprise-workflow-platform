#!/usr/bin/env python3
"""
初始化数据库数据脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.base import SessionLocal, Base, engine
from app.models.user import User, Role, Permission, Department, Tenant
from app.models.component import ComponentCategory
from app.models.workflow import WorkflowCategory
from app.core.security import get_password_hash


def init_permissions(db: Session):
    """初始化权限数据"""
    permissions = [
        # 系统管理
        {"name": "用户管理", "code": "user:manage", "resource_type": "menu"},
        {"name": "角色管理", "code": "role:manage", "resource_type": "menu"},
        {"name": "权限管理", "code": "permission:manage", "resource_type": "menu"},
        
        # 工作流
        {"name": "工作流查看", "code": "workflow:view", "resource_type": "menu"},
        {"name": "工作流创建", "code": "workflow:create", "resource_type": "button"},
        {"name": "工作流编辑", "code": "workflow:update", "resource_type": "button"},
        {"name": "工作流删除", "code": "workflow:delete", "resource_type": "button"},
        {"name": "工作流执行", "code": "workflow:execute", "resource_type": "button"},
        
        # 组件
        {"name": "组件查看", "code": "component:view", "resource_type": "menu"},
        {"name": "组件创建", "code": "component:create", "resource_type": "button"},
        {"name": "组件编辑", "code": "component:update", "resource_type": "button"},
        {"name": "组件删除", "code": "component:delete", "resource_type": "button"},
        {"name": "组件发布", "code": "component:publish", "resource_type": "button"},
    ]
    
    for perm_data in permissions:
        existing = db.query(Permission).filter(Permission.code == perm_data["code"]).first()
        if not existing:
            perm = Permission(**perm_data)
            db.add(perm)
    
    db.commit()
    print("✅ 权限数据初始化完成")


def init_roles(db: Session):
    """初始化角色数据"""
    # 管理员角色
    admin_role = db.query(Role).filter(Role.code == "admin").first()
    if not admin_role:
        admin_role = Role(
            name="管理员",
            code="admin",
            description="系统管理员，拥有所有权限",
            role_type="system"
        )
        db.add(admin_role)
        db.flush()
        
        # 分配所有权限
        all_permissions = db.query(Permission).all()
        admin_role.permissions = all_permissions
    
    # 普通用户角色
    user_role = db.query(Role).filter(Role.code == "user").first()
    if not user_role:
        user_role = Role(
            name="普通用户",
            code="user",
            description="普通用户，可查看和执行工作流",
            role_type="system"
        )
        db.add(user_role)
        db.flush()
        
        # 分配查看和执行权限
        view_perms = db.query(Permission).filter(
            Permission.code.in_([
                "workflow:view", "workflow:execute",
                "component:view"
            ])
        ).all()
        user_role.permissions = view_perms
    
    # 开发者角色
    dev_role = db.query(Role).filter(Role.code == "developer").first()
    if not dev_role:
        dev_role = Role(
            name="开发者",
            code="developer",
            description="开发人员，可管理工作流和组件",
            role_type="system"
        )
        db.add(dev_role)
        db.flush()
        
        # 分配开发相关权限
        dev_perms = db.query(Permission).filter(
            Permission.code.in_([
                "workflow:view", "workflow:create", "workflow:update", "workflow:delete", "workflow:execute",
                "component:view", "component:create", "component:update", "component:publish"
            ])
        ).all()
        dev_role.permissions = dev_perms
    
    db.commit()
    print("✅ 角色数据初始化完成")
    return admin_role, user_role


def init_tenant(db: Session):
    """初始化租户"""
    tenant = db.query(Tenant).filter(Tenant.code == "default").first()
    if not tenant:
        tenant = Tenant(
            name="默认租户",
            code="default",
            description="系统默认租户",
            is_active=True,
            settings={},
            limits={
                "max_users": 100,
                "max_workflows": 1000,
                "max_components": 500,
                "max_executions_per_day": 10000
            }
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    
    print("✅ 租户数据初始化完成")
    return tenant


def init_admin_user(db: Session, tenant: Tenant):
    """初始化管理员用户"""
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin_role = db.query(Role).filter(Role.code == "admin").first()
        
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="系统管理员",
            is_active=True,
            is_superuser=True,
            is_verified=True,
            tenant_id=tenant.id
        )
        admin.roles = [admin_role] if admin_role else []
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("✅ 管理员用户初始化完成")
        print("   用户名: admin")
        print("   密码: admin123")
    else:
        print("✅ 管理员用户已存在")
    
    return admin


def init_component_categories(db: Session):
    """初始化组件分类"""
    categories = [
        {"name": "基础组件", "code": "basic", "icon": "AppstoreOutlined", "category_type": "system"},
        {"name": "API组件", "code": "api", "icon": "ApiOutlined", "category_type": "system"},
        {"name": "数据库", "code": "database", "icon": "DatabaseOutlined", "category_type": "system"},
        {"name": "消息队列", "code": "message", "icon": "MessageOutlined", "category_type": "system"},
        {"name": "AI组件", "code": "ai", "icon": "RobotOutlined", "category_type": "system"},
        {"name": "控制流", "code": "control", "icon": "ControlOutlined", "category_type": "system"},
        {"name": "MCP组件", "code": "mcp", "icon": "CloudOutlined", "category_type": "system"},
    ]
    
    for cat_data in categories:
        existing = db.query(ComponentCategory).filter(ComponentCategory.code == cat_data["code"]).first()
        if not existing:
            cat = ComponentCategory(**cat_data)
            db.add(cat)
    
    db.commit()
    print("✅ 组件分类初始化完成")


def init_workflow_categories(db: Session):
    """初始化工作流分类"""
    categories = [
        {"name": "业务流程", "icon": "ContainerOutlined", "color": "#1890ff"},
        {"name": "数据处理", "icon": "DatabaseOutlined", "color": "#52c41a"},
        {"name": "定时任务", "icon": "ClockCircleOutlined", "color": "#faad14"},
        {"name": "AI应用", "icon": "RobotOutlined", "color": "#722ed1"},
        {"name": "系统集成", "icon": "CloudOutlined", "color": "#13c2c2"},
    ]
    
    for cat_data in categories:
        existing = db.query(WorkflowCategory).filter(WorkflowCategory.name == cat_data["name"]).first()
        if not existing:
            cat = WorkflowCategory(**cat_data)
            db.add(cat)
    
    db.commit()
    print("✅ 工作流分类初始化完成")


def main():
    """主函数"""
    print("🚀 开始初始化数据库数据...")
    
    # 创建表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    
    db = SessionLocal()
    try:
        # 按顺序初始化
        init_permissions(db)
        init_roles(db)
        tenant = init_tenant(db)
        init_admin_user(db, tenant)
        init_component_categories(db)
        init_workflow_categories(db)
        
        print("\n✨ 所有数据初始化完成！")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
