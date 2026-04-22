"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from src.config.settings import settings

# Get database URL from settings
database_url = settings.database_url

# Handle different database types
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Sync engine for migrations
engine = create_engine(database_url, connect_args={"check_same_thread": False} if "sqlite" in database_url else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine for FastAPI
if "sqlite" in database_url:
    async_database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(async_database_url)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with async_engine.begin() as conn:
        # Import all models here to ensure they are registered
        from src.models import user, portfolio, transaction, mock_trading
        await conn.run_sync(Base.metadata.create_all)