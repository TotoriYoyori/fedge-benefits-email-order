from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Optional

from bs4 import BeautifulSoup
from fastapi import Query
from pydantic import EmailStr, Field, field_validator, model_validator

from src.notification.exceptions import EmailResponseMismatch
from src.schemas import CustomBaseModel, QueryModel


# =============== ENUM SCHEMAS ===============
class EmailProviderName(StrEnum):
    """Only supports either 'resend' or 'mailtrap' modes.

    Resend should be used for all production environments, while mailtrap is for development and testing.
    """
    RESEND = "resend"
    MAILTRAP = "mailtrap"


# =============== INPUT SCHEMAS ===============
class EmailSendRequest(CustomBaseModel):
    """
    Schema for sending a notification email to a customer.

    Example:
        >>> {
        ...     "name": "Cloud Strife",
        ...     "to_email": "customer@example.com",
        ...     "treatment": "massage",
        ...     "location": "Stockholm",
        ...     "order_number": "order_number_123",
        ...     "subject_line": "Du har redan bestallt friskvardsbehandling hos oss. Boka nu!",
        ... }
    """

    name: Optional[str] = None
    to_email: EmailStr
    treatment: Annotated[str, Field(min_length=1, max_length=128)] = "en eller flera behandlingar"
    location: Annotated[str, Field(min_length=1, max_length=128)] = "en av vara kliniker"
    order_number: Annotated[Optional[str], Field(description="Order number, vary per provider")] = None
    subject_line: Annotated[str, Field(min_length=1, max_length=64)] = (
        "Du har redan best\u00e4llt friskv\u00e5rdsbehandling hos oss. Boka nu!"
    )

# =============== QUERY SCHEMAS ===============
class TemplatePreviewQuery(QueryModel):
    """
    Query parameters for previewing a rendered notification email template.

    Example:
        >>> {
        ...     "name": "Cloud Strife",
        ...     "treatment": "en eller flera behandlingar",
        ...     "location": "en av vara kliniker",
        ...     "order_number": "order_number_123",
        ... }
    """

    name: Annotated[Optional[str], Query(max_length=64)] = "Cloud Strife"
    treatment: Annotated[Optional[str], Query(max_length=255)] = "en eller flera behandlingar"
    location: Annotated[Optional[str], Query(max_length=255)] = "en av vara kliniker"
    order_number: Annotated[Optional[str], Query(max_length=255)] = "order_number_123"


# =============== ADAPTER SCHEMAS ===============
class EmailProviderPayload(CustomBaseModel):
    """
    Adapter payload sent to the configured email provider.

    Example:
        >>> {
        ...     "to_email": "customer@example.com",
        ...     "subject_line": "Du har redan bestallt friskvardsbehandling hos oss. Boka nu!",
        ...     "html_body": "<p>Thank you for your order.</p>",
        ...     "plain_body": "Thank you for your order.",
        ... }
    """

    to_email: str
    subject_line: str
    html_body: str
    plain_body: str

    @field_validator("html_body")
    @classmethod
    def validate_html_body(cls, value: str) -> str:
        soup = BeautifulSoup(value, "html.parser")

        if soup.find() is None:
            raise ValueError("html_body must contain valid HTML markup.")

        return value


# =============== OUTPUT SCHEMAS ===============
class EmailSendResponse(CustomBaseModel):
    """
    App-facing adapter for email provider send responses.

    Example:
        >>> {
        ...     "id": "8a965505-63a6-4068-b4b2-d1d7da98788b",
        ...     "status": "accepted",
        ...     "accepted_at": "2026-05-12T21:51:50+00:00",
        ...     "daily_quota": 0,
        ...     "monthly_quota": 22,
        ...     "provider": "resend",
        ...     "message": "Notification email accepted for delivery.",
        ... }
    """

    id: str | None = None
    status: str = "accepted"
    accepted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    daily_quota: Optional[int] = None
    monthly_quota: Optional[int] = None
    provider: EmailProviderName
    message: str = "Notification email accepted for delivery."

    @model_validator(mode="before")
    @classmethod
    def parse_provider_metadata[ProviderResponse](cls, data: ProviderResponse) -> ProviderResponse:
        payload = dict(data)
        http_headers = {key.lower(): value for key, value in payload.pop("http_headers", {}).items()}

        if payload.get("provider") != EmailProviderName.RESEND or not http_headers:
            return payload

        try:
            payload["daily_quota"] = int(http_headers["x-resend-daily-quota"])
            payload["monthly_quota"] = int(http_headers["x-resend-monthly-quota"])
        except (TypeError, ValueError, IndexError, AttributeError, KeyError) as exc:
            raise EmailResponseMismatch from exc

        return payload
