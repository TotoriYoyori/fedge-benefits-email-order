from typing import Annotated, Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import (
    AlreadyAuthenticated,
    InsufficientPermission,
    InvalidCredentials,
    UsernameAlreadyExists,
)
from src.auth.models import User
from src.auth.schemas import AuthCreate
from src.auth.service import (
    decode_access_token,
    get_user_by,
    oauth2_scheme,
    verify_password,
    verify_token,
)
from src.database import get_db


# =============== USER AUTHENTICATION DEPENDENCIES ===============
async def valid_login_credentials(
    login_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Validate username and password from an urlencoded form.

    Use as dependency injection only.

    Raises:
        InvalidCredentials: If the username does not exist or the password is invalid.

    Example:
        >>> async def login(valid_login_user: Annotated[User, Depends(valid_login_credentials)]):
        >>>    if not valid_login_user:
        >>>        return None
        >>>    return valid_login_user
    """
    user = await get_user_by("username", login_form.username, db)
    if not user or not verify_password(login_form.password, user.password_hash):
        raise InvalidCredentials

    return user


async def valid_access_token(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Validate a JWT access token embedded in Headers from request.

    Use as dependency injection only.

    Raises:
        UnauthenticatedUser: If the token is missing.
        MalformedToken: If the token is invalid or malformed.
        UserNotFound: If no user matches the token new_credential.

    Example:
        >>> async def me(authorized_user: Annotated[User, Depends(valid_access_token)]):
        >>>     return authorized_user
    """
    return await verify_token(token, db)


def require_role(*roles: str) -> Callable:
    """
    Enforce role-based access control via Bearer token authentication.

    Args:
        *roles (str): One or more role names permitted to access the resource.

    Returns:
        Callable: A dependency function checker() that validates the user's role and
        returns the authenticated user or raises.

    Raises:
        InsufficientPermission: If the authenticated user does not have one of the required roles.

    Example:
        >>> async def send_notify_email(
        >>>     valid_login_user: Annotated[User, Depends(require_role("merchant", "admin"))],
        >>>     send_context: EmailSendRequest
        >>> ) -> None:
    """

    async def checker(user: Annotated[User, Depends(valid_access_token)]) -> User:
        if user is None or user.role not in roles:
            raise InsufficientPermission

        return user

    return checker


# =============== AUTHENTICATION STATUS CHECKS ===============
async def not_currently_logged_in(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> bool | None:
    """
    Prevent authenticated users from accessing public auth routes (e.g., login, register).

    Checking JWT token embedded in Headers. Use as dependency injection only.

    Raises:
        AlreadyAuthenticated: If a valid token is present, indicating the user is already logged in.

    Example:
        >>> @router.post("/", dependencies=[Depends(not_currently_logged_in)])
        >>> async def register():
    """
    if token and decode_access_token(token):
        raise AlreadyAuthenticated

    return True


async def username_already_exists(
    auth_create: AuthCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> bool:
    """
    Check if a username already exists during registration by what user inputs during registration.

    Use as dependency injection only.

    Raises:
        UsernameAlreadyExists: If the username is already taken.

    Example:
        >>> async def register(
        >>>     username_taken: Annotated[bool, Depends(username_already_exists)],
        >>> ) -> User | None:
    """
    user = await get_user_by("username", auth_create.username, db)
    if user:
        raise UsernameAlreadyExists

    return False
