from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import AuthCreate
from src.auth.service import create_user, get_user_by, verify_password


async def test_auth_service_create_user(session: AsyncSession):
    auth_create = AuthCreate(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    user = await create_user(auth_create, session)

    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert verify_password("password123", user.password_hash)
    assert user.role == "user"


async def test_auth_service_get_one_by(session: AsyncSession):
    auth_create = AuthCreate(
        username="lookupuser",
        email="lookup@example.com",
        password="password123"
    )
    await create_user(auth_create, session)

    user = await get_user_by("username", "lookupuser", session)
    assert user is not None
    assert user.username == "lookupuser"

    none_user = await get_user_by("username", "nonexistent", session)
    assert none_user is None
