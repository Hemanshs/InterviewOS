import uuid
from collections.abc import AsyncGenerator

import asyncpg
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

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


async def get_or_create_user(
    session: AsyncSession,
    user_id: str,
    email: str | None = None,
) -> str:
    """
    Upsert a local user row for the authenticated Supabase user.
    """
    effective_email = email or f"{user_id}@interviewos.local"

    user_uuid = uuid.UUID(user_id)
    existing = await session.execute(select(User).where(User.id == user_uuid))
    user = existing.scalar_one_or_none()
    if user is not None:
        if user.email != effective_email:
            user.email = effective_email
            await session.commit()
        return str(user.id)

    user = User(id=user_uuid, email=effective_email)
    session.add(user)
    await session.commit()
    return user_id
