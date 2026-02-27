"""
健康检查工具模块
用于检查数据库连接池和 RabbitMQ 连接状态
"""
import asyncio
from typing import Dict, Any
from sqlalchemy import text
from loguru import logger
from db_wrapper import async_engine
from core.config.settings import settings

# 健康检查超时时间（秒）
HEALTH_CHECK_TIMEOUT = 3  # 3秒超时，确保快速响应


async def check_database_connection() -> Dict[str, Any]:
    """
    检查数据库连接池状态
    返回连接池状态信息
    使用超时控制，避免长时间等待
    """
    try:
        pool = async_engine.pool
        # 获取连接池状态（只使用可用的属性）
        status = {
            "status": "ok",
        }
        
        # 尝试获取连接池统计信息（快速操作，不需要超时）
        try:
            status["pool_size"] = pool.size()
        except (AttributeError, TypeError):
            status["pool_size"] = None
            
        try:
            status["checked_in"] = pool.checkedin()
        except (AttributeError, TypeError):
            status["checked_in"] = None
            
        try:
            status["checked_out"] = pool.checkedout()
        except (AttributeError, TypeError):
            status["checked_out"] = None
            
        try:
            status["overflow"] = pool.overflow()
        except (AttributeError, TypeError):
            status["overflow"] = None
        
        # 尝试执行一个简单的查询来验证连接是否真的可用
        # 使用超时控制，避免连接超时时长时间等待
        try:
            # 使用 asyncio.wait_for 确保兼容性（支持 Python 3.7+）
            async def _test_connection():
                async with async_engine.connect() as conn:
                    result = await conn.execute(text("SELECT 1"))
                    # fetchone() 是同步方法，不需要 await
                    # 使用 scalar() 直接获取标量值更简洁
                    value = result.scalar()
                    if value == 1:
                        return "ok"
                    else:
                        return "failed"
            
            connection_test_result = await asyncio.wait_for(
                _test_connection(),
                timeout=HEALTH_CHECK_TIMEOUT
            )
            status["connection_test"] = connection_test_result
            if connection_test_result != "ok":
                status["status"] = "error"
        except asyncio.TimeoutError:
            logger.warning(f"Database connection check timeout after {HEALTH_CHECK_TIMEOUT}s")
            status["connection_test"] = "timeout"
            status["status"] = "timeout"
            status["error"] = f"Connection test timeout after {HEALTH_CHECK_TIMEOUT} seconds"
        except Exception as conn_error:
            logger.error(f"Database connection test failed: {str(conn_error)}")
            status["connection_test"] = "failed"
            status["status"] = "error"
            status["error"] = str(conn_error)
        
        return status
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "pool_size": None,
            "checked_in": None,
            "checked_out": None,
            "overflow": None,
            "connection_test": "failed"
        }
