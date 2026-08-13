import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import exceptions as auth_exceptions
from src.auth.dependencies import (
    require_role,
    username_already_exists,
    valid_access_token,
)
from src.auth.schemas import AuthCreate
from src.auth.service import create_user, create_access_token


async def test_dependency_username_already_exists(session: AsyncSession):
    auth_create = AuthCreate(
        username="exists",
        email="e@e.com",
        password="password123"
    )
    await create_user(auth_create, session)
    
    # This should raise UsernameAlreadyExists exception
    with pytest.raises(auth_exceptions.UsernameAlreadyExists):
        await username_already_exists(auth_create, session)


async def test_dependency_valid_access_token_success(session: AsyncSession):
    auth_create = AuthCreate(
        username="tokenuser",
        email="t@e.com",
        password="password123"
    )
    user = await create_user(auth_create, session)
    
    token_obj = create_access_token(
        {"sub": str(user.id), "role": user.role}
    )
    
    validated_user = await valid_access_token(token_obj.access_token, session)
    assert validated_user.id == user.id


async def test_dependency_require_role_failure(session: AsyncSession):
    auth_create = AuthCreate(
        username="regularuser",
        email="r@e.com",
        password="password123"
    )
    user = await create_user(auth_create, session)
    
    checker = require_role("admin")
    with pytest.raises(auth_exceptions.InsufficientPermission):
        await checker(user)
