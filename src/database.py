from typing import Annotated, AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

# --------------- ALEMBIC MIGRATION NAMING CONVENTION
NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


# --------------- ORM ENTITY BASE CLASS
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# --------------- ASYNC ENGINE AND SESSION FACTORY
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DB_ECHO)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async database session for request handling. Use as dependency injector only.

    Yields:
        AsyncSession: Active database session. Will cleanup after finish.

    Example:
        >>> async def endpoint(db: Annotated[AsyncSession, Depends(get_db)]):
        ...     result = await db.execute(select(User))
    """
    # ----- Initialize Async Context
    async with AsyncSessionLocal() as session:
        yield session
