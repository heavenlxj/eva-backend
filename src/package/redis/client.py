#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : client.py

from redis.asyncio import Redis, ConnectionPool
from core.config.settings import settings
from contextlib import asynccontextmanager
from loguru import logger

# 全局连接池（单例模式）
_redis_pool: ConnectionPool | None = None
_redis_client: Redis | None = None


def get_redis_pool() -> ConnectionPool:
    """获取全局 Redis 连接池（单例）"""
    global _redis_pool
    if _redis_pool is None:
        logger.info("Creating Redis connection pool", extra={
            "max_connections": 50,
            "redis_url": settings.redis.URL.split("@")[-1] if "@" in settings.redis.URL else "hidden"
        })
        _redis_pool = ConnectionPool.from_url(
            settings.redis.URL,
            max_connections=50,  # 最大连接数
            decode_responses=False,  # 根据需求设置
        )
        logger.info("Redis connection pool created successfully")
    else:
        logger.debug("Reusing existing Redis connection pool")
    return _redis_pool


def get_redis_client() -> Redis:
    """获取全局 Redis 客户端（单例）"""
    global _redis_client
    if _redis_client is None:
        logger.info("Creating Redis client with connection pool")
        pool = get_redis_pool()
        _redis_client = Redis(connection_pool=pool)
        logger.info("Redis client created successfully")
    else:
        logger.debug("Reusing existing Redis client")
    return _redis_client


@asynccontextmanager
async def new_asyncio_redis_client():
    """
    获取 Redis 客户端（使用连接池）
    使用 async with 确保连接正确归还到连接池
    
    注意：使用连接池时，连接会自动管理，不需要手动关闭
    """
    client = get_redis_client()
    logger.debug("Getting Redis client from connection pool")
    try:
        yield client
    except Exception as e:
        logger.error(f"Error using Redis client: {str(e)}", exc_info=True)
        raise
    finally:
        logger.debug("Redis client operation completed, connection returned to pool")


async def close_redis_connections():
    """关闭所有 Redis 连接（应用关闭时调用）"""
    global _redis_client, _redis_pool
    
    if _redis_client:
        try:
            logger.info("Closing Redis client...")
            await _redis_client.aclose()
            _redis_client = None
            logger.info("Redis client closed successfully")
        except Exception as e:
            logger.error(f"Error closing Redis client: {str(e)}", exc_info=True)
    
    if _redis_pool:
        try:
            # 记录连接池关闭前的状态
            pool_stats = {}
            try:
                if hasattr(_redis_pool, '_created_connections'):
                    pool_stats['created_connections'] = _redis_pool._created_connections
                if hasattr(_redis_pool, '_available_connections'):
                    pool_stats['available_connections'] = len(_redis_pool._available_connections)
                if hasattr(_redis_pool, '_in_use_connections'):
                    pool_stats['in_use_connections'] = _redis_pool._in_use_connections
            except Exception:
                # 如果无法获取连接池状态，忽略错误
                pass
            
            if pool_stats:
                logger.info("Closing Redis connection pool...", extra=pool_stats)
            else:
                logger.info("Closing Redis connection pool...")
            
            await _redis_pool.aclose()
            _redis_pool = None
            logger.info("Redis connection pool closed successfully")
        except Exception as e:
            logger.error(f"Error closing Redis connection pool: {str(e)}", exc_info=True)
    
    # 注意：关闭连接池会自动关闭所有连接
