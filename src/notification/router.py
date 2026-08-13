from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import HTMLResponse

from src.auth.dependencies import require_role
from src.auth.models import User

from src.notification.schemas import (
    EmailSendRequest,
    EmailSendResponse,
    TemplatePreviewQuery,
)
from src.notification.service import send_email
from src.notification.service.email import write_email_html


# =============== ROUTER ===============
router = APIRouter(prefix="/api/v1/notification", tags=["api-notification"])


@router.post(
    "/",
    response_model=EmailSendResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a notification email",
    responses={
        200: {"description": "Notification email sent successfully"},
        404: {"description": "Not found."},
        422: {"description": "Invalid request body"},
    },
)
async def send_notify_email(
    _valid_user: Annotated[User, Depends(require_role("merchant", "admin"))],
    send_request: EmailSendRequest,
):
    return await send_email(send_request)


@router.get(
    "/templates",
    response_class=HTMLResponse,
    name="preview_notification_template_api",
    summary="Render a notification email template preview",
)
async def preview_email_template(
    preview_order: Annotated[TemplatePreviewQuery, Depends()],
):
    preview_request = EmailSendRequest(
        name=preview_order.name,
        to_email="preview@fedge-demo-studio.com",
        treatment=preview_order.treatment or "en eller flera behandlingar",
        location=preview_order.location or "en av vara kliniker",
        order_number=preview_order.order_number,
    )
    return HTMLResponse(content=write_email_html(preview_request))
