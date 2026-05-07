import uuid
from collections.abc import AsyncGenerator

import asyncpg
from fastapi import Request
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
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
    If a previously deleted account returns with the same email, revive the row
    while preserving its prior usage limits.
    """
    effective_email = email or f"{user_id}@interviewos.local"

    user_uuid = uuid.UUID(user_id)
    existing = await session.execute(
        select(User).where(or_(User.id == user_uuid, User.email == effective_email))
    )
    users = list(existing.scalars().all())

    user_by_id = next((user for user in users if user.id == user_uuid), None)
    if user_by_id is not None:
        if user_by_id.deleted_at is not None:
            user_by_id.deleted_at = None
        if user_by_id.email != effective_email:
            user_by_id.email = effective_email
        await session.commit()
        return str(user_by_id.id)

    user_by_email = next((user for user in users if user.email == effective_email), None)
    if user_by_email is not None:
        if user_by_email.deleted_at is not None:
            user_by_email.id = user_uuid
            user_by_email.deleted_at = None
            await session.commit()
            return str(user_by_email.id)
        return str(user_by_email.id)

    user = User(id=user_uuid, email=effective_email)
    session.add(user)
    try:
        await session.commit()
        return user_id
    except IntegrityError:
        await session.rollback()
        existing = await session.execute(
            select(User).where(or_(User.id == user_uuid, User.email == effective_email))
        )
        recovered_users = list(existing.scalars().all())

        recovered_by_id = next(
            (existing_user for existing_user in recovered_users if existing_user.id == user_uuid),
            None,
        )
        if recovered_by_id is not None:
            if recovered_by_id.deleted_at is not None:
                recovered_by_id.deleted_at = None
                await session.commit()
            return str(recovered_by_id.id)

        recovered_by_email = next(
            (
                existing_user
                for existing_user in recovered_users
                if existing_user.email == effective_email
            ),
            None,
        )
        if recovered_by_email is not None:
            return str(recovered_by_email.id)

        raise
