from src.notification.schemas import (
    EmailProviderPayload,
    EmailSendRequest,
    EmailSendResponse,
)
from src.notification.service.client import email_provider, send_with_provider
from src.notification.service.email import write_email_html, write_email_plaintext

# =============== SENDING EMAIL FLOWS ===============
async def send_email(send_request: EmailSendRequest) -> EmailSendResponse:
    """
    Compose and send a notification email through the configured provider.

    Args:
        send_request: User-facing request data used to render the notification
            email subject, HTML body, and plain-text body.

    Returns:
        EmailSendResponse: App-facing response returned after the configured
        provider accepts the notification email for delivery.

    Example:
        >>> async def run_example() -> str:
        ...     response = await send_email(send_request)
        ...     return response.status
    """

    html_body = write_email_html(send_request)
    plain_body = write_email_plaintext(send_request)
    provider_payload = EmailProviderPayload(
        to_email=send_request.to_email,
        subject_line=send_request.subject_line,
        html_body=html_body,
        plain_body=plain_body,
    )

    return await send_with_provider(email_provider, provider_payload)
