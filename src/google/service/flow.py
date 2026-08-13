from sqlalchemy.ext.asyncio import AsyncSession

from src.google.models import GoogleOAuthCredential, GoogleOAuthState

from src.google.service.client import (
    build_google_oauth_state,
    fetch_google_oauth_credential,
    get_gmail_service,
    fetch_refreshed_google_oauth_credential,
)
from src.google.service.crud import (
    create_or_replace_state,
    create_oauth_credential,
    get_oauth_credential,
    patch_oauth_credential,
    refresh_oauth_access_token,
    update_oauth_credential,
)
from src.google.service.gmail import get_current_user_email


# =============== OAUTH2 INITIATE AND EXCHANGE FLOW ===============
async def initiate_oauth2(db: AsyncSession, valid_user_id: int) -> GoogleOAuthState:
    """Replace any lingering OAuth state and persist a fresh one for the user.

    Args:
        db: Active async database session used to clear prior state rows and store
            the newly generated OAuth state.
        valid_user_id: App ID of the authenticated user starting the Google OAuth flow.

    Returns:
        GoogleOAuthState: Newly created OAuth state user_google_credential containing
            the authorization URL and persisted app-side state after any
            previous unconsumed state for the same user has been removed.
    """
    new_state = await build_google_oauth_state(valid_user_id)

    return await create_or_replace_state(db, new_state)


async def exchange_code_for_credentials(
    db: AsyncSession,
    exchange_code: str,
    oauth_state: GoogleOAuthState,
) -> GoogleOAuthCredential:
    """Exchange a callback code and persist the resulting Google OAuth user_google_credential.

    Args:
        db: Active async database session used for user_google_credential lookup and writes.
        exchange_code: Authorization code returned by Google in the callback.
        oauth_state: Persisted OAuth states user_google_credential that scopes the exchange. The
            state user_google_credential is consumed by the downstream create or update operation
            once user_google_credential persistence succeeds.

    Returns:
        GoogleOAuthCredential: Persisted Google OAuth user_google_credential user_google_credential created
        or updated for the user.

    Example:
        >>> async def run_example() -> int:
        ...     user_google_credential = await exchange_code_for_credentials(
        ...         db, exchange_code, current_oauth_state
        ...     )
        ...     return user_google_credential.user_id
    """
    current_credential = await get_oauth_credential(db, oauth_state.user_id)

    new_credential = await fetch_google_oauth_credential(exchange_code, oauth_state)
    if current_credential is None:
        return await create_oauth_credential(db, new_credential, oauth_state)

    return await update_oauth_credential(db, current_credential, new_credential, oauth_state)


# =============== REFRESH FLOW ===============
async def sync_access_token(
    db: AsyncSession,
    user_google_credential: GoogleOAuthCredential,
) -> GoogleOAuthCredential:
    refreshed_credential = await fetch_refreshed_google_oauth_credential(user_google_credential)
    if (
        refreshed_credential.access_token == user_google_credential.access_token
        and refreshed_credential.expiry == user_google_credential.expiry
    ):
        return user_google_credential

    return await refresh_oauth_access_token(db, user_google_credential, refreshed_credential)


# =============== FLOW TO SYNC WITH GOOGLE'S SERVICES ===============
async def connect_gmail_service(
    db: AsyncSession,
    user_google_credential: GoogleOAuthCredential,
) -> GoogleOAuthCredential:
    user_google_credential = await sync_access_token(db, user_google_credential)

    service = await get_gmail_service(user_google_credential)
    email_address = await get_current_user_email(service)

    return await patch_oauth_credential(
        db,
        user_google_credential,
        {"email_address": email_address},
    )
