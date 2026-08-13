from typing import AsyncGenerator

from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.auth.models import User  # noqa: F401
from src.auth.schemas import AuthCreate
from src.auth.service import create_user, create_access_token
from src.database import Base, get_db
from src.google.models import GoogleOAuthCredential, GoogleOAuthState  # noqa: F401
from src.main import app


# =============== DATABASE FIXTURES ===============
@pytest_asyncio.fixture(name="session")
async def test_session() -> AsyncGenerator[AsyncSession]:
    test_engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


# =============== HTTP CLIENT FIXTURES ===============
@pytest_asyncio.fixture(name="client")
async def test_client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def get_db_override():
        yield session

    app.dependency_overrides[get_db] = get_db_override

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


# =============== AUTH FIXTURES ===============
@pytest_asyncio.fixture(name="jwt_token")
async def test_jwt_token(session: AsyncSession):
    async def _create(role: str = "user") -> str:
        user = await create_user(
            AuthCreate(
                username=f"test_user_{role}",
                email=f"test_{role}@example.com",
                password="password123",
            ),
            session,
        )
        user.role = role
        await session.commit()

        token_obj = create_access_token(
            data={"sub": str(user.id), "role": user.role}
        )
        return token_obj.access_token

    return _create


# =============== OVERRIDE FIXTURES ===============
@pytest.fixture
def override_dependency(request):
    def _factory(dependency, value):
        async def _override():
            return value

        app.dependency_overrides[dependency] = _override
        request.addfinalizer(lambda: app.dependency_overrides.pop(dependency, None))

        return value

    return _factory
