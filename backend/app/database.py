"""
Database configuration and session management
Using SQLAlchemy 2.0 with async support
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine (for FastAPI endpoints)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.is_development,  # Log SQL queries in development
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Test connections before using
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create sync engine (for RQ workers)
# Convert asyncpg URL to psycopg2 for sync
sync_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

sync_engine = create_engine(
    sync_url,
    echo=settings.is_development,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# Create sync session factory (for RQ workers)
SessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False,
)

# Create declarative base
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI endpoints
    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    from fastapi import HTTPException

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except HTTPException:
            # HTTPException is a valid response, not a database error
            # Re-raise it without rollback
            raise
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create all tables
    NOTE: In production, use Alembic migrations instead
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created")


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("👋 Database connections closed")
