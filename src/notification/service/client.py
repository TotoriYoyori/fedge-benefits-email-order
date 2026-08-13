from email.utils import formatdate, make_msgid
from typing import Any, Protocol

import asyncer
import mailtrap as mt
import resend
from requests import RequestException
from resend.exceptions import NoContentError, ResendError

from src.notification.exceptions import EmailDeliveryError
from src.notification.schemas import (
    EmailProviderName,
    EmailProviderPayload,
    EmailSendResponse,
)
from src.notification.settings import notification_settings as ns


# =============== EMAIL PROVIDER PROTOCOLS ===============
class EmailProvider[ProviderParams](Protocol):
    """
    Common shape for every email provider client.

    Each provider knows how to turn our app's email payload into the format
    its own service needs, then send that email through its own API.

    Example:
        >>> async def deliver_notification(
        ...     provider: EmailProvider[ProviderParams],
        ...     provider_payload: EmailProviderPayload,
        ... ) -> EmailSendResponse:
        ...     params = provider.build(provider_payload)
        ...     return await provider.send(params)
    """
    def build(self, provider_payload: EmailProviderPayload) -> ProviderParams:
        pass

    async def send(self, params: ProviderParams) -> EmailSendResponse:
        pass


async def send_with_provider[ProviderParams](
    provider: EmailProvider[ProviderParams],
    provider_payload: EmailProviderPayload,
) -> EmailSendResponse:
    """
    Send an email using whichever provider the app is configured to use.

    Args:
        provider: Email service client, such as Resend or Mailtrap. The app
            only needs it to follow the EmailProvider protocol.
        provider_payload: Email message data from our app, before it has been
            changed into the provider's own format.

    Returns:
        EmailSendResponse: App-friendly response after the provider accepts
        the email for delivery.

    Example:
        >>> async def run_example() -> EmailSendResponse:
        ...     return await send_with_provider(email_provider, provider_payload)
    """
    params = provider.build(provider_payload)

    return await provider.send(params)


# =============== RESEND EMAIL PROVIDER ===============
class ResendEmailProvider:
    """
    Email provider client for sending real notification emails through Resend.

    This class knows how to turn our app's email payload into Resend's send
    parameters, then send those parameters through the Resend API.
    """

    def __init__(self) -> None:
        resend.api_key = ns.RESEND_API_KEY

    def build(self, payload: EmailProviderPayload) -> resend.Emails.SendParams:
        params = {
            "from": ns.email_from,
            "to": [payload.to_email],
            "subject": payload.subject_line,
            "html": payload.html_body,
            "text": payload.plain_body,
            "headers": {"Message-ID": make_msgid(), "Date": formatdate(localtime=True)},
        }
        return resend.Emails.SendParams(params)

    async def send(self, params: resend.Emails.SendParams) -> EmailSendResponse:
        try:
            response = await asyncer.asyncify(resend.Emails.send)(params)
        except (ResendError, NoContentError) as exc:
            raise EmailDeliveryError from exc

        return EmailSendResponse.model_validate(
            {
                **response,
                "provider": EmailProviderName.RESEND,
            }
        )


# =============== MAILTRAP EMAIL PROVIDER ===============
class MailtrapEmailProvider:
    """
    Email provider client for sending test emails through Mailtrap sandbox.

    This class uses Mailtrap's sandbox inbox so development and test emails can
    be inspected without sending real messages to customers.
    """

    def __init__(self) -> None:
        self._mailtrap = mt
        self._client = mt.MailtrapClient(
            token=str(ns.MAILTRAP_API_KEY),
            sandbox=True,
            inbox_id=str(ns.MAILTRAP_SANDBOX_INBOX_ID),
        )

    def build(self, payload: EmailProviderPayload) -> Any:
        params = {
            "sender": self._mailtrap.Address(
                email=str(ns.EMAIL_FROM_ADDRESS),
                name=ns.EMAIL_FROM_NAME,
            ),
            "to": [self._mailtrap.Address(email=payload.to_email)],
            "subject": payload.subject_line,
            "html": payload.html_body,
            "text": payload.plain_body,
            "category": "Notification",
        }

        return self._mailtrap.Mail(**params)

    async def send(self, params: Any) -> EmailSendResponse:
        try:
            response = await asyncer.asyncify(self._client.send)(params)
        except (self._mailtrap.MailtrapError, RequestException) as exc:
            raise EmailDeliveryError from exc

        return EmailSendResponse(
            id=self._extract_message_id(response),
            provider=EmailProviderName.MAILTRAP,
            message="Notification email accepted by Mailtrap sandbox.",
        )

    @staticmethod
    def _extract_message_id(response: Any) -> str | None:
        if isinstance(response, dict):
            message_ids = response.get("message_ids") or []
            return str(message_ids[0]) if message_ids else None

        message_ids = getattr(response, "message_ids", None) or []
        return str(message_ids[0]) if message_ids else None


# =============== START ONCE ON SERVICE INITIALIZATION ===============
def get_email_provider() -> EmailProvider[Any]:
    """
    Return the email provider selected by notification settings.

    Returns:
        EmailProvider[Any]: Mailtrap in sandbox mode when configured, otherwise
        Resend for real email delivery.

    Example:
        >>> provider = get_email_provider()
        >>> isinstance(provider, EmailProvider)
        True
    """

    if ns.EMAIL_PROVIDER == EmailProviderName.MAILTRAP:
        return MailtrapEmailProvider()

    return ResendEmailProvider()


email_provider = get_email_provider()
