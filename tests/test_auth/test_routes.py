from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import AuthCreate
from src.auth.service import create_user, create_access_token


async def test_route_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    assert response.json()["username"] == "newuser"


async def test_route_register_duplicate_username(client: AsyncClient, session: AsyncSession):
    # --- Pre-register a user
    await create_user(
        AuthCreate(username="duplicate", email="d1@e.com", password="password123"),
        session
    )
    
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "duplicate",
            "email": "d2@e.com",
            "password": "password123"
        }
    )

    # Deliberately indistinguishable from any other bad /register input —
    # this endpoint never confirms that a username is taken.
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request."}


async def test_route_login_success(client: AsyncClient, session: AsyncSession):
    await create_user(
        AuthCreate(username="loginuser", email="l@e.com", password="password123"),
        session
    )
    
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "loginuser", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_route_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "wronguser", "password": "wrongpassword"}
    )
    # Deliberately indistinguishable from a malformed login request — this
    # endpoint never confirms whether the username exists.
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request."}


async def test_route_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    # A missing token collapses into the same generic "not found" response as
    # an invalid token or a deleted user — never a distinguishable 401.
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}


async def test_route_me_success(client: AsyncClient, session: AsyncSession):
    # Register and login to get access_token
    user = await create_user(
        AuthCreate(username="meuser", email="me@example.com", password="password123"),
        session
    )
    token_obj = create_access_token({"sub": str(user.id), "role": user.role})
    
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_obj.access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "meuser"
    # UserPrivate must never leak the password hash to the client.
    assert "passwordHash" not in data
    assert "registrationTime" in data
    assert "message" in data
    assert data["message"] == "Welcome back, master Wick ..."


async def test_route_register_with_extra_fields(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "extrafieldsuser",
            "email": "extra@example.com",
            "password": "password123",
            "malicious_field": "hacking_attempt",
            "internal_flag": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "extrafieldsuser"
    assert "malicious_field" not in data
    assert "internal_flag" not in data

# Note: the source project also had a `test_login_form_uses_https` test here,
# exercising a server-rendered `/login` HTML page. That SSR layer isn't part
# of this extraction (API-only, see README), so the route no longer exists
# and the test was dropped rather than adapted.
