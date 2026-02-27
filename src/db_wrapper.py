from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from core.config.settings import settings

host = settings.mysql.HOST
port = settings.mysql.PORT
dbname = settings.mysql.DATABASE
username = settings.mysql.USERNAME
password = settings.mysql.PASSWORD
echo = settings.mysql.ECHO
pool_size = settings.mysql.POOL_SIZE
max_size = settings.mysql.MAX_OVERFLOW
pool_recycle = settings.mysql.POOL_RECYCLE
pool_timeout = settings.mysql.POOL_TIMEOUT

# Base class for ORM models
class Base(DeclarativeBase):
    pass

# Configure the async engine for MySQL
async_engine = create_async_engine(
    f"mysql+aiomysql://{username}:{password}@{host}:{port}/{dbname}",
    echo=echo,
    pool_recycle=pool_recycle,  # auto recycle connection
    pool_pre_ping=True,         # auto check connection is available
    pool_size=pool_size,        # connection pool size
    max_overflow=max_size,      # max connection over pool size
    pool_timeout=pool_timeout,  # connection pool get timeout
    pool_use_lifo=True         # use LIFO to manage connection pool, better handle sudden traffic

)

# Create a session factory for asynchronous sessions
# AsyncSessionLocal = sessionmaker(
#     bind=async_engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
# )

# 2.0 supports async session maker
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

# Dependency for getting an async database session
async def async_get_db() -> AsyncSession:
    async with AsyncSessionLocal() as db:
        yield db


DB_SESSION = Annotated[AsyncSession, Depends(async_get_db)]