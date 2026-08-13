from typing import Annotated

from fastapi import APIRouter, Depends, status
# FIXME: Codesmell google being imported in router.py
from googleapiclient.discovery import Resource
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_role
from src.auth.models import User
from src.database import get_db
from src.google.dependencies import (
    valid_google_oauth2_exchange_code,
    valid_google_oauth2_state,
    valid_google_oauth_credential,
    valid_gmail_service,
)
from src.google.models import GoogleOAuthCredential, GoogleOAuthState
from src.google.service import (
    connect_gmail_service,
    initiate_oauth2,
    exchange_code_for_credentials,
    get_gmail_messages,
)
from src.google.schemas import (
    GmailInboxQuery,
    GmailInboxResponse,
    GoogleOAuth2CredentialResponse,
    GoogleOAuth2RedirectResponse,
)
from src.schemas import PaginationQuery


# =============== API ROUTER ===============
router = APIRouter(prefix="/api/v1/google", tags=["api-google"])


@router.post(
    "/oauth2",
    summary="Create Google OAuth2 authorization state",
    description=(
        "Creates a temporary OAuth2 state `new_state` for the authenticated user and "
        "returns the Google authorization URL (`auth_url`) the client should use to redirect "
        "the user."
    ),
    response_model=GoogleOAuth2RedirectResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "model": GoogleOAuth2RedirectResponse,
            "description": "Successfully created OAuth2 authorization state",
        },
        401: {"description": "Unauthorized access"},
        403: {"description": "Insufficient permissions"},
    },
)
async def oauth2(
    valid_user: Annotated[User, Depends(require_role("merchant", "admin"))],
    db: AsyncSession = Depends(get_db),
):
    return await initiate_oauth2(db, valid_user.id)


@router.get(
    "/callback",
    summary="Handle Google OAuth2 callback",
    description=(
        "Consumes the Google OAuth2 callback, validates the returned state, "
        "and exchanges the authorization code for Google OAuth2 new_credential."
    ),
    response_model=GoogleOAuth2CredentialResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "model": GoogleOAuth2CredentialResponse,
            "description": "Successfully exchanged the callback code for new_credential",
        },
        400: {"description": "Malformed callback or invalid state"},
    },
)
async def callback(
    exchange_code: Annotated[str, Depends(valid_google_oauth2_exchange_code)],
    oauth_state: Annotated[GoogleOAuthState, Depends(valid_google_oauth2_state)],
    db: AsyncSession = Depends(get_db),
):
    return await exchange_code_for_credentials(db, exchange_code, oauth_state)


@router.get(
    "/me",
    summary="Get the current user's Google OAuth2 new_credential",
    description=(
        "Validates that the authenticated user has a persisted Google OAuth2 user_google_credential "
        "and returns the current user_google_credential user_credential."
    ),
    response_model=GoogleOAuth2CredentialResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "model": GoogleOAuth2CredentialResponse,
            "description": "Successfully validated and returned the user's Google OAuth2 user_google_credential",
        },
        404: {"description": "Google OAuth user_google_credential not found for app user"},
    },
)
async def me(
    user_google_credential: Annotated[GoogleOAuthCredential, Depends(valid_google_oauth_credential)],
):
    return user_google_credential


@router.post(
    "/gmail",
    response_model=GoogleOAuth2CredentialResponse,
    status_code=status.HTTP_200_OK,
    summary="Connect Gmail service",
    description=(
        "Builds the Gmail service and syncs profile data using previously persisted "
        "Google OAuth2 new_credential."
    ),
    responses={
        200: {
            "model": GoogleOAuth2CredentialResponse,
            "description": "Successfully synced Google OAuth2 new_credential with Gmail",
        },
        404: {"description": "Google OAuth user_google_credential not found for app user"},
    },
)
async def gmail(
    user_google_credential: Annotated[GoogleOAuthCredential, Depends(valid_google_oauth_credential)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await connect_gmail_service(db, user_google_credential)


# =============== GMAIL ROUTES ===============
@router.get(
    "/inbox",
    response_model=GmailInboxResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch Gmail inbox messages",
    description=(
        "Fetches the user's Gmail inbox messages using the provided Gmail service. "
        "Supports pagination and filtering by query parameters."
    ),
    responses={
        200: {
            "model": GmailInboxResponse,
            "description": "Successfully fetched Gmail inbox messages",
        },
        404: {"description": "No Gmail messages found for the user"},
    },
)
async def get_inbox_messages(
    gmail_service: Annotated[Resource, Depends(valid_gmail_service)],
    query: Annotated[GmailInboxQuery, Depends()],
    pagination: Annotated[PaginationQuery, Depends()],
):
    return await get_gmail_messages(gmail_service, pagination, query)
