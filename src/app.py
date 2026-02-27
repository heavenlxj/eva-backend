import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sys
import traceback
from loguru import logger
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from core.exception import PlatformException
from core.error_code import ErrorCode
from core.config.settings import settings
from contextlib import asynccontextmanager
from api.router import api_router
from core.middleware import ClientVerificationMiddleware
from db_wrapper import async_engine
from core.rabbitmq import RabbitMQClient
from core.health_check import check_database_connection
from package.redis.client import close_redis_connections


logger.remove()


logger.add(
    sys.stdout, 
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


logger.add(
    "logs/app_{time:YYYY-MM-DD_HH}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="1 hour",
    retention="30 days",
    encoding="utf-8",
    level="DEBUG"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    logger.info("Shutting down connections...")
    logger.info("Closing Redis connections...")
    await close_redis_connections()
    logger.info("Redis connections closed.")
    logger.info("Shutting down database connections...")
    await async_engine.dispose()
    logger.info("Database connections closed.")

app = FastAPI(lifespan=lifespan)

@app.exception_handler(PlatformException)
async def platform_exception_handler(request: Request, exc: PlatformException):
    """处理平台自定义异常"""
    logger.warning(f"PlatformException: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=200,
        content=exc.detail
    )

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc):
    """处理所有其他未捕获的异常"""
    status_code = 500
    error_code = 10000
    
    logger.error(f"{str(exc)} - Path: {request.url.path}")
    error_msg = {"code": error_code, "data": None, "message": str(exc)}
    
    return JSONResponse(status_code=status_code, content=error_msg)

# CORS 中间件必须在最前面，确保预检请求（OPTIONS）能通过
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境建议配置具体域名
    allow_credentials=False,  # 当 allow_origins=["*"] 时，allow_credentials 必须为 False
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.api.ENABLE_CLIENT_VERIFICATION:
    app.add_middleware(ClientVerificationMiddleware)

app.include_router(api_router)

@app.get("/health")
async def health():
    """
    快速健康检查端点
    用于 Kubernetes liveness/readiness 探针
    不检查外部依赖，确保快速响应（< 100ms）
    """
    return {"status": "ok"}


@app.get("/health/database")
async def health_database():
    """
    检查数据库连接池状态
    """
    try:
        db_status = await check_database_connection()
        status_code = 200 if db_status.get("status") == "ok" else 503
        return JSONResponse(status_code=status_code, content=db_status)
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": str(e)
            }
        )


if __name__ == '__main__':
    uvicorn.run(app, 
                host=settings.server.HOST, 
                port=settings.server.PORT, 
                log_level=settings.server.LOG_LEVEL
    )
