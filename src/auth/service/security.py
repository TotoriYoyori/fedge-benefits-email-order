from datetime import UTC, datetime, timedelta
import json

from fastapi.security import OAuth2PasswordBearer
import jwt
from pwdlib import PasswordHash

from src.auth.schemas import Token
from src.auth.settings import auth_settings

# =============== SECURITY PRIMITIVES ===============
password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# =============== JWT AND CRYPTOGRAPHY SERVICES ===============
def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_token_expiry_timestamp(
    expires_delta: timedelta | None = None,
) -> datetime:
    """
    Calculate the datetime for when a JWT access token will expire.

    Args:
        expires_delta (timedelta | None): Optional custom duration for token validity.
            If not provided, the default value from settings is used.

    Returns:
        datetime: The computed expiration timestamp in UTC.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    return datetime.now(UTC) + expires_delta


def get_access_token_max_age_seconds() -> int:
    return auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> Token:
    """
    Create a JWT access token with an expiration timestamp of type bearer.
    """
    to_encode = data.copy()
    expire = get_token_expiry_timestamp(expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        auth_settings.SECRET_KEY.get_secret_value(),
        algorithm=auth_settings.ALGORITHM,
    )

    return Token(access_token=encoded_jwt, token_type="bearer")


def assign_role(role_key: str | None) -> str:
    """
    Assign a user role based on an optional role key.
    """
    role = "user"
    if role_key:
        try:
            role_keys = json.loads(auth_settings.DEV_ROLE_KEYS)
            if role_key in role_keys:
                role = role_keys[role_key]
        except (json.JSONDecodeError, TypeError):
            pass

    return role


def decode_access_token(token: str) -> dict | None:
    """
    Decode a JWT access token and return its payload if valid.
    """
    try:
        payload = jwt.decode(
            token,
            auth_settings.SECRET_KEY.get_secret_value(),
            algorithms=[auth_settings.ALGORITHM],
            options={"require": ["exp", "sub", "role"]},
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload
