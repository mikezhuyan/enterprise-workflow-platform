from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, components, workflows, dashboard, approvals, schedules, webhooks
from app.api.v1.endpoints.webhooks import workflow_router as webhook_workflow_router, webhook_router, public_router
from app.api.v1.endpoints.schedules import schedule_router

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(components.router, prefix="/components", tags=["组件管理"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["工作流管理"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["审批管理"])
api_router.include_router(schedules.router, prefix="/workflows", tags=["定时任务管理"])
api_router.include_router(schedule_router, prefix="/schedules", tags=["定时任务管理"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])

# Webhook管理路由
api_router.include_router(webhook_workflow_router, prefix="/workflows", tags=["Webhook管理"])
api_router.include_router(webhook_router, prefix="/webhooks", tags=["Webhook管理"])
# 公共Webhook触发路由 (单独处理，在main.py中注册到根路径)
