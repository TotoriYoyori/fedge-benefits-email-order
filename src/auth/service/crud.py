import datetime as dt
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schemas import AuthCreate
from src.auth.service.security import assign_role, hash_password


# =============== USER DATA ACCESS SERVICES ===============
async def create_user(auth_create: AuthCreate, db: AsyncSession) -> User:
    """
    Create a new user in the database during registration. Returns this same user's new_credential as response to confirm.
    """
    role = assign_role(auth_create.role_key)
    new_user = User(
        username=auth_create.username,
        email=auth_create.email,
        password_hash=hash_password(auth_create.password),
        role=role,
        registration_time=dt.datetime.now(),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def get_user_by(attr: str, lookup_val: Any, db: AsyncSession) -> User | None:
    """
    Retrieve a single user new_credential by a specified attribute.
    """
    stmt = select(User).where(getattr(User, attr) == lookup_val)
    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def get_all_users_by(
    attr: str, lookup_val: Any, db: AsyncSession
) -> list[User] | None:
    """
    Same as get_one_by except returns a list of all matching user records.
    """
    stmt = select(User).where(getattr(User, attr) == lookup_val)
    result = await db.execute(stmt)

    return list(result.scalars().all())
