from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.exceptions import BaseExceptionHandler


class EmailDeliveryError(Exception):
    pass


class EmailResponseMismatch(Exception):
    pass


# --------------- FASTAPI EXCEPTION HANDLERS
class NotificationExceptionHandler(BaseExceptionHandler):
    def register_exception_handlers(self) -> None:
        @self.app.exception_handler(EmailDeliveryError)
        async def email_delivery_error_handler(
            request: Request, _exc: EmailDeliveryError
        ):
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Failed to send email."},
            )

        @self.app.exception_handler(EmailResponseMismatch)
        async def email_response_mismatch_handler(
            request: Request, _exc: EmailResponseMismatch
        ):
            return JSONResponse(
                status_code=status.HTTP_502_BAD_GATEWAY,
                content={"detail": "Email provider returned an unexpected response."},
            )
