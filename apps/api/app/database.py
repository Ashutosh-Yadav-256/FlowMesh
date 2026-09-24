from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool
from app.config import settings

db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

if "postgresql" in db_url:
    try:
        import asyncpg  # noqa
        engine = create_async_engine(
            db_url,
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
    except ImportError:

        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
else:
    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
        poolclass=StaticPool if ":memory:" in db_url else None,
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarative class for all FlowMesh models."""
    pass


_tables_initialized = False


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a tenant-safe transactional database session."""
    global _tables_initialized
    if not _tables_initialized:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _tables_initialized = True

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
