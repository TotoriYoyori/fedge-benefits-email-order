from datetime import UTC, date, datetime
from typing import Annotated, Optional
from urllib.parse import urlparse, parse_qs

from fastapi import Query
from pydantic import (
    EmailStr,
    Field,
    ValidationInfo,
    field_serializer,
    field_validator,
)

from src.schemas import CustomBaseModel, QueryModel
from src.google.exceptions import (
    InvalidGoogleOAuthCallbackState,
    InvalidGoogleOAuthCredential
)


# =============== APP LAYER CREATION SCHEMA FOR OAUTH STATE AND OAUTH CREDENTIALS ===============
class GoogleOAuth2StateCreate(CustomBaseModel):
    """
    Schema for the app-side payload used to create a Google OAuth state user_google_credential.

    Example:
        >>> {
        ...     "state": "abc123state",
        ...     "auth_url": "https://accounts.google.com/o/oauth2/auth?state=abc123state?code_challenge=test-challenge",
        ...     "user_id": 42,
        ...     "code_verifier": "pkce-code-verifier-value",
        ...     "created_time": "2026-05-04T12:45:00Z"
        ... }
    """

    state: str
    auth_url: str
    user_id: int
    code_verifier: str
    created_time: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("created_time", mode="before")
    @classmethod
    def normalize_utc(cls, value:datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)

    @field_validator("auth_url", mode="before")
    @classmethod
    def auth_url_from_google(cls, value: str) -> str:
        if not value.startswith("https://accounts.google.com/o/oauth2/auth"):
            raise InvalidGoogleOAuthCallbackState

        parsed_url = urlparse(value)
        params = parse_qs(parsed_url.query)

        if not {"state", "code_challenge"}.issubset(params):
            raise InvalidGoogleOAuthCallbackState

        return value


class GoogleOAuth2CredentialCreate(CustomBaseModel):
    """
    Schema for the app-side payload used to create or update Google OAuth new_credential.

    Example:
        >>> {
        ...     "user_id": 42,
        ...     "access_token": "ya29.a0AfH6SMExample",
        ...     "refresh_token": "1//0gExampleRefreshToken",
        ...     "token_uri": "https://oauth2.googleapis.com/token",
        ...     "client_id": "google-client-id.apps.googleusercontent.com",
        ...     "client_secret": "client-secret-value",
        ...     "scopes": "openid,email,https://www.googleapis.com/auth/gmail.readonly",
        ...     "expiry": "2026-05-04T12:30:00Z",
        ...     "email_address": "merchant@example.com"
        ... }
    """

    user_id: int
    access_token: str
    refresh_token: Optional[str] = Field(default=None)
    token_uri: str
    client_id: str
    client_secret: str
    scopes: str
    expiry: Optional[datetime] = Field(default=None)
    email_address: Optional[EmailStr] = Field(default=None)

    created_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_time: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("created_time", "updated_time", "expiry", mode="before")
    @classmethod
    def normalize_utc(cls, value:datetime) -> datetime:
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)

# =============== USER FACING RESPONSE SCHEMA ===============
class GoogleOAuth2RedirectResponse(CustomBaseModel):
    """
    Schema for the response returned when starting the Google OAuth2 flow.

    Example:
        >>> {
        ...     "auth_url": "https://accounts.google.com/o/oauth2/auth?state=abc123",
        ...     "message": "You are being redirected to Google for authorization."
        ... }
    """

    auth_url: str
    message: str = "You are being redirected to Google for authorization."


class GoogleOAuth2CredentialResponse(CustomBaseModel):
    """
    Schema for the response returned after Google OAuth new_credential are stored or synced.

    Example:
        >>> {
        ...     "user_id": 42,
        ...     "scopes": "openid,email,https://www.googleapis.com/auth/gmail.readonly",
        ...     "expiry": "2026-05-04T12:30:00Z",
        ...     "message": "Successfully connected to Google using OAuth 2.0!"
        ... }
    """

    user_id: int
    scopes: str
    expiry: Optional[datetime] = Field(default=None)
    email_address: Optional[EmailStr] = Field(default=None)
    message: str = "Successfully connected to Google using OAuth 2.0!"


# =============== INBOX SCHEMAS ===============
class GmailInboxQuery(QueryModel):
    """
    Schema for Gmail inbox search filters accepted by the inbox listing endpoint.

    Example:
        >>> {
        ...     "from": "fps@benify.com",
        ...     "label": "inbox",
        ...     "after": "2026-05-01",
        ...     "before": "2026-05-10"
        ... }
    """

    from_: Annotated[Optional[str], Query(alias="from", min_length=1, pattern=r"^\S+$")] = None
    label: Annotated[Optional[str], Query(min_length=1, pattern=r"^\S+$")] = None
    after: Annotated[Optional[date], Query(examples=["2026-05-01"])] = None
    before: Annotated[Optional[date], Query(examples=["2026-05-10"])] = None

    @field_validator("before")
    @classmethod
    def validate_date_range(cls, before: date | None, info: ValidationInfo) -> date | None:
        after = info.data.get("after")
        if after is not None and before is not None and after > before:
            raise ValueError("after must not be later than before")

        return before

    @field_serializer("from_", "label", "after", "before", when_used="json")
    def serialize_gmail_query_field(self, value, info) -> str | None:
        if value is None:
            return None

        value_text = value.isoformat() if isinstance(value, date) else value.strip()

        return f"{info.field_name.removesuffix('_')}:{value_text}"

    def to_gmail_query(self) -> str | None:
        """Return None when no filters are set so Gmail performs its default fetch."""
        query_parts = self.model_dump(mode="json", exclude_none=True).values()

        return " ".join(query_parts) or None


class GmailMessageResponse(CustomBaseModel):
    """
    Schema for a single Gmail message returned from the inbox listing endpoint.

    Example:
        >>> {
        ...     "subject": "Your order confirmation",
        ...     "sender": "store@example.com",
        ...     "to": "merchant@example.com",
        ...     "cc": None,
        ...     "body": "Thank you for your order.",
        ...     "receive_time": "Sun, 03 May 2026 09:15:00 +0000",
        ...     "label_ids": ["INBOX", "UNREAD"]
        ... }
    """

    subject: Optional[str] = Field(default=None)
    sender: Optional[EmailStr] = Field(default=None)
    to: Optional[EmailStr] = Field(default=None)
    cc: Optional[EmailStr] = Field(default=None)
    body: Optional[str] = Field(default=None)
    receive_time: Optional[str] = Field(default=None, max_length=998)
    label_ids: list[Annotated[str, Field(min_length=1, max_length=255)]] = Field(
        default_factory=list,
        max_length=100,
    )


class GmailInboxResponse(CustomBaseModel):
    """
    Schema for the response returned when listing Gmail inbox messages.

    Example:
        >>> {
        ...     "messages": [
        ...         {
        ...             "subject": "Your order confirmation",
        ...             "sender": "store@example.com",
        ...             "to": "merchant@example.com",
        ...             "cc": None,
        ...             "body": "Thank you for your order.",
        ...             "receive_time": "Sun, 03 May 2026 09:15:00 +0000",
        ...             "label_ids": ["INBOX", "UNREAD"]
        ...         }
        ...     ],
        ...     "result_size_estimate": 1
        ... }
    """

    messages: list[GmailMessageResponse]
    result_size_estimate: int | None = Field(default=None)
