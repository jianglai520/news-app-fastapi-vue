import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ASYNC_DATABASE_URL = os.getenv("DATABASE_URL")   # async_database_url 添加到了 .env 防止泄露
if not ASYNC_DATABASE_URL:
    raise RuntimeError(f"缺少 DATABASE_URL，请在 {BASE_DIR / '.env'} 里配置")

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
)


AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def close_db():
    await async_engine.dispose()