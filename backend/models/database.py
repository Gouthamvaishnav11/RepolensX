from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models.db_models import Base
from config import settings
from loguru import logger


def _async_url(url: str) -> str:
    """Ensure URL uses asyncpg driver."""
    if "postgresql+asyncpg" in url:
        return url
    return url.replace("postgresql://", "postgresql+asyncpg://").replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://"
    )


def _sync_url(url: str) -> str:
    """Ensure URL uses psycopg2 driver."""
    return url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


async_engine = create_async_engine(
    _async_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

sync_engine = create_engine(
    _sync_url(settings.DATABASE_URL),
    echo=False,
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created successfully")


async def drop_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("⚠️ All database tables dropped")
