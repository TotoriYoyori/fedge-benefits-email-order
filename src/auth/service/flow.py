from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import MalformedToken, UnauthenticatedUser, UserNotFound
from src.auth.models import User
from src.auth.service.crud import get_user_by
from src.auth.service.security import decode_access_token


async def verify_token(access_token: str | None, db: AsyncSession) -> User:
    if not access_token:
        raise UnauthenticatedUser

    payload = decode_access_token(access_token)
    if not payload:
        raise MalformedToken

    user_id = payload.get("sub")
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise MalformedToken

    user = await get_user_by("id", user_id_int, db)
    if not user:
        raise UserNotFound

    return user
