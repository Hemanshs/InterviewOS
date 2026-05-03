import uuid
from collections.abc import AsyncGenerator

import asyncpg
from fastapi import Request
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from app.core.config import get_settings
from app.models.user import User

settings = get_settings()


def get_sqlalchemy_database_url() -> str:
    if settings.DATABASE_URL.startswith("postgresql+asyncpg://"):
        return settings.DATABASE_URL

    if settings.DATABASE_URL.startswith("postgresql://"):
        return settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

    return settings.DATABASE_URL


async_engine = create_async_engine(
    get_sqlalchemy_database_url(),
    echo=settings.DEBUG,
    poolclass=NullPool,
    connect_args={"prepared_statement_cache_size": 0},
)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


async def connect_to_database():
    return await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        statement_cache_size=0,
    )


async def close_database_pool(pool: asyncpg.Pool | None) -> None:
    if pool is not None:
        await pool.close()


async def get_db(request: Request):
    pool: asyncpg.Pool = request.app.state.db_pool
    async with pool.acquire() as connection:
        yield connection


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_or_create_dev_user(session: AsyncSession) -> str:
    """
    Get or create the dev user for mock auth.
    TODO: Remove when real auth is implemented.
    """
    existing = await session.execute(
        select(User).where(User.email == settings.DEV_USER_EMAIL)
    )
    user = existing.scalar_one_or_none()
    if user is not None:
        return str(user.id)

    user = User(
        id=uuid.UUID(settings.DEV_USER_ID),
        email=settings.DEV_USER_EMAIL,
    )
    session.add(user)
    await session.commit()
    return settings.DEV_USER_ID
