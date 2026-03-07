from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, components, workflows, dashboard

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(components.router, prefix="/components", tags=["组件管理"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["工作流管理"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])
