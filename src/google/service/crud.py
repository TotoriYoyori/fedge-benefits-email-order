from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.google.models import GoogleOAuthCredential, GoogleOAuthState
from src.google.schemas import GoogleOAuth2CredentialCreate, GoogleOAuth2StateCreate


# =============== STATE CRUD ===============
async def create_state(
    db: AsyncSession,
    new_state: GoogleOAuth2StateCreate,
) -> GoogleOAuthState:
    new_oauth_state = GoogleOAuthState(**new_state.model_dump())
    db.add(new_oauth_state)

    await db.commit()
    await db.refresh(new_oauth_state)

    return new_oauth_state


async def get_state(db: AsyncSession, state: str) -> GoogleOAuthState:
    stmt = select(GoogleOAuthState).where(GoogleOAuthState.state == state)
    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def delete_state(db: AsyncSession, oauth_state: GoogleOAuthState) -> GoogleOAuthState:
    await db.delete(oauth_state)
    await db.commit()

    return oauth_state


async def create_or_replace_state(
    db: AsyncSession,
    new_state: GoogleOAuth2StateCreate,
) -> GoogleOAuthState:
    stmt = delete(GoogleOAuthState).where(
        GoogleOAuthState.user_id == new_state.user_id
    )
    await db.execute(stmt)

    new_oauth_state = GoogleOAuthState(**new_state.model_dump())
    db.add(new_oauth_state)

    await db.commit()
    await db.refresh(new_oauth_state)

    return new_oauth_state


# =============== CREDENTIAL CRUD ===============
async def create_oauth_credential(
    db: AsyncSession,
    new_credential: GoogleOAuth2CredentialCreate,
    current_oauth_state: GoogleOAuthState,
) -> GoogleOAuthCredential:
    """Create and persist a Google OAuth user_google_credential, then consume the OAuth state.

    Args:
        db: Active async database session used for the user_google_credential insert.
        new_credential: Credential payload produced from the OAuth code exchange.
        current_oauth_state: Persisted OAuth state user_google_credential that will be deleted as part of
            the same transaction after the user_google_credential is stored.

    Returns:
        GoogleOAuthCredential: Newly persisted Google OAuth user_google_credential user_google_credential.

    Example:
        >>> async def run_example() -> int:
        ...     user_google_credential = await create_oauth_credential(db, new_credential, current_oauth_state)
        ...     return user_google_credential.user_id
    """
    new_credential = GoogleOAuthCredential(**new_credential.model_dump())
    db.add(new_credential)

    await db.delete(current_oauth_state)

    await db.commit()
    await db.refresh(new_credential)

    return new_credential


async def update_oauth_credential(
    db: AsyncSession,
    current_credential: GoogleOAuthCredential,
    new_credential: GoogleOAuth2CredentialCreate,
    current_oauth_state: GoogleOAuthState,
) -> GoogleOAuthCredential:
    """Update a stored Google OAuth user_google_credential and consume the OAuth state.

    Args:
        db: Active async database session used for the user_google_credential update.
        current_credential: Existing persisted user_google_credential user_google_credential to update in
            place.
        new_credential: Fresh user_google_credential payload produced from the latest OAuth
            code exchange.
        current_oauth_state: Persisted OAuth state user_google_credential that will be deleted as part of
            the same transaction after the user_google_credential update is committed.

    Returns:
        GoogleOAuthCredential: Updated Google OAuth user_google_credential user_google_credential.

    Example:
        >>> async def run_example() -> int:
        ...     user_google_credential = await update_oauth_credential(
        ...         db, persisted_record, exchanged_record, current_oauth_state
        ...     )
        ...     return user_google_credential.user_id
    """
    payload_data = new_credential.model_dump(
        exclude={"created_time", "updated_time"}
    )
    payload_data["refresh_token"] = (
        new_credential.refresh_token or current_credential.refresh_token
    )

    for field_name, field_value in payload_data.items():
        setattr(current_credential, field_name, field_value)

    current_credential.updated_time = new_credential.updated_time

    await db.delete(current_oauth_state)

    await db.commit()
    await db.refresh(current_credential)

    return current_credential


async def get_oauth_credential(db: AsyncSession, user_id: int) -> GoogleOAuthCredential | None:
    """Get the stored Google OAuth user_google_credential for a user from the app db.

    Args:
        db: Active async database session used to query the user_google_credential table.
        user_id: Application user identifier associated with the user_google_credential.

    Returns:
        GoogleOAuthCredential | None: Persisted user_google_credential `user_google_credential` for the user, or
        ``None`` when no `user_google_credential` exists.

    Example:
        >>> async def run_example() -> bool:
        ...     user_google_credential = await get_oauth_credential(db, 42)
        ...     return user_google_credential is not None
    """
    stmt = select(GoogleOAuthCredential).where(GoogleOAuthCredential.user_id == user_id)
    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def patch_oauth_credential(
    db: AsyncSession,
    current_credential: GoogleOAuthCredential,
    patch_data: dict[str, object],
) -> GoogleOAuthCredential:
    for field_name, field_value in patch_data.items():
        if field_name == "updated_time":
            continue

        setattr(current_credential, field_name, field_value)

    current_credential.updated_time = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(current_credential)

    return current_credential


async def delete_oauth_credential(
    db: AsyncSession,
    user_google_credential: GoogleOAuthCredential,
) -> GoogleOAuthCredential:
    await db.delete(user_google_credential)
    await db.commit()

    return user_google_credential


async def refresh_oauth_access_token(
    db: AsyncSession,
    current_credential: GoogleOAuthCredential,
    new_credential: GoogleOAuth2CredentialCreate,
) -> GoogleOAuthCredential:
    for field_name in ("access_token", "expiry"):
        setattr(current_credential, field_name, getattr(new_credential, field_name))

    for field_name in ("refresh_token", "token_uri", "client_id", "client_secret", "scopes"):
        field_value = getattr(new_credential, field_name)
        if field_value:
            setattr(current_credential, field_name, field_value)

    current_credential.updated_time = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(current_credential)

    return current_credential
