from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

from app.core.config import settings
from app.api.v1.router import api_router
from app.api.v1.endpoints.webhooks import public_router as webhook_public_router
from app.db.base import DatabaseManager, SessionLocal
from app.services.scheduler_service import SchedulerService

# 创建FastAPI应用
def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="企业级智能工作流平台 API",
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
    )
    
    # 添加中间件
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Gzip压缩
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 请求日志和追踪
    @app.middleware("http")
    async def add_request_metadata(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": str(exc) if settings.DEBUG else "服务器内部错误",
                "request_id": getattr(request.state, "request_id", None)
            }
        )
    
    # 注册路由
    app.include_router(api_router, prefix="/api/v1")
    
    # 注册公共Webhook路由 (无需认证)
    app.include_router(webhook_public_router, prefix="/webhooks", tags=["Webhook公共端点"])
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "timestamp": time.time()
        }
    
    # 根路径
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/api/docs"
        }
    
    return app


app = create_application()


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    # 初始化数据库表
    DatabaseManager.init_db()
    print("✅ 数据库初始化完成")
    
    # 初始化定时调度器
    SchedulerService.initialize(settings.DATABASE_URL)
    
    # 从数据库加载活动的定时任务
    db = SessionLocal()
    try:
        SchedulerService.load_all_schedules(db)
    finally:
        db.close()


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    # 关闭定时调度器
    SchedulerService.shutdown()
    print(f"👋 {settings.APP_NAME} 已关闭")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
