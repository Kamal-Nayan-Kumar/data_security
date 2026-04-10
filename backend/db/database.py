import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


raw_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/vget",
)

# Render provides postgres:// or postgresql:// by default, but asyncpg requires postgresql+asyncpg://
if raw_url.startswith("postgres://"):
    DATABASE_URL = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif raw_url.startswith("postgresql://") and not raw_url.startswith(
    "postgresql+asyncpg://"
):
    DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = raw_url

engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
