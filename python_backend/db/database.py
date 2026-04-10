import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/vget",
)

engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
