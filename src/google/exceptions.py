from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.exceptions import BaseExceptionHandler

GENERIC_VALIDATION_ERROR = {"detail": "Invalid request."}
GENERIC_NOT_FOUND_ERROR = {"detail": "Not found."}


# =============== DOMAIN EXCEPTIONS ===============
class FaultyFlow(Exception):
    """Server-side misconfiguration (the OAuth flow itself couldn't be built)."""
    pass


class ClientSecretNotFound(Exception):
    """Server-side misconfiguration (missing OAuth client secret)."""
    pass


class InvalidGoogleOAuthCallbackState(Exception):
    """The callback's `code`/`state` query params were missing, unknown, or expired."""
    pass


class InvalidPKCE(Exception):
    pass


class InvalidGoogleOAuthCredential(Exception):
    """No usable Google OAuth credential for this user (never connected, or stale)."""
    pass


# =============== EXCEPTION HANDLERS ===============
class GoogleExceptionHandler(BaseExceptionHandler):


    def register_exception_handlers(self) -> None:
        @self.app.exception_handler(ClientSecretNotFound)
        async def client_secret_not_found_handler(
            request: Request, _exc: ClientSecretNotFound
        ):
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Google OAuth client secret file was not found."},
            )

        @self.app.exception_handler(FaultyFlow)
        async def faulty_flow_handler(request: Request, _exc: FaultyFlow):
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": (
                        "Google OAuth flow, authorization URL, or state could not "
                        "be created."
                    )
                },
            )

        # ----- callback input problems
        @self.app.exception_handler(InvalidGoogleOAuthCallbackState)
        @self.app.exception_handler(InvalidPKCE)
        async def callback_validation_handler(request: Request, _exc: Exception):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content=GENERIC_VALIDATION_ERROR,
            )

        # ----- credential/identity problems
        @self.app.exception_handler(InvalidGoogleOAuthCredential)
        async def invalid_google_oauth_credential_handler(
            request: Request, _exc: InvalidGoogleOAuthCredential
        ):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=GENERIC_NOT_FOUND_ERROR,
            )
