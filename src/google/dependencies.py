from typing import Annotated

from fastapi import Depends, Query
from googleapiclient.discovery import Resource
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_role
from src.auth.models import User
from src.database import get_db
from src.google.exceptions import (
    InvalidGoogleOAuthCredential,
    InvalidGoogleOAuthCallbackState,
)
from src.google.models import GoogleOAuthCredential, GoogleOAuthState
from src.google.service import (
    credential_is_stale,
    get_gmail_service,
    get_oauth_credential,
    get_state,
    state_is_stale,
    sync_access_token,
)


# =============== CALLBACK CHECKS ===============
def valid_google_oauth2_exchange_code(
    exchange_code_in_query: Annotated[str | None, Query(alias="code")] = None,
) -> str:
    if not exchange_code_in_query:
        raise InvalidGoogleOAuthCallbackState

    return exchange_code_in_query


async def valid_google_oauth2_state(
    db: Annotated[AsyncSession, Depends(get_db)],
    state_in_query: Annotated[str | None, Query(alias="state")] = None,
) -> GoogleOAuthState:
    if not state_in_query:
        raise InvalidGoogleOAuthCallbackState

    oauth_state = await get_state(db, state_in_query)
    if oauth_state is None:
        raise InvalidGoogleOAuthCallbackState

    if state_is_stale(oauth_state):
        raise InvalidGoogleOAuthCallbackState

    return oauth_state

# =============== CREDENTIAL CHECKS ===============
async def valid_google_oauth_credential(
    valid_user: Annotated[User, Depends(require_role("merchant", "admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GoogleOAuthCredential:
    """Return the authenticated user's usable Google OAuth credential.

    Returns:
        GoogleOAuthCredential: Persisted Google OAuth credential for the user.

    Raises:
        InvalidGoogleOAuthCredential: If no credential exists or the stored
            credential is stale.
    """
    user_google_credential = await get_oauth_credential(db, valid_user.id)
    if user_google_credential is None:
        raise InvalidGoogleOAuthCredential

    if credential_is_stale(user_google_credential):
        raise InvalidGoogleOAuthCredential

    return user_google_credential


async def valid_gmail_service(
    user_google_credential: Annotated[GoogleOAuthCredential, Depends(valid_google_oauth_credential)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Resource:
    if user_google_credential.email_address is None:
        raise InvalidGoogleOAuthCredential

    synced_credential = await sync_access_token(db, user_google_credential)

    return await get_gmail_service(synced_credential)
