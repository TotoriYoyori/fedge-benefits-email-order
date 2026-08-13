from abc import ABC, abstractmethod

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


GENERIC_VALIDATION_ERROR = {"detail": "Invalid request."}


class BaseExceptionHandler(ABC):
    """Shared exception handler utilities. Domain handlers inherit and extend this."""

    def __init__(self, app):
        self.app = app
        self.register_exception_handlers()

    @abstractmethod
    def register_exception_handlers(self) -> None:
        """Override in each domain to register domain-specific handlers."""


class HttpExceptionHandler(BaseExceptionHandler):
    def register_exception_handlers(self) -> None:
        @self.app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(
            request: Request, exc: StarletteHTTPException
        ):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=getattr(exc, "headers", None),
            )

        @self.app.exception_handler(RequestValidationError)
        async def request_validation_error_handler(
            request: Request, _exc: RequestValidationError
        ):
            return JSONResponse(
                status_code=422,
                content=GENERIC_VALIDATION_ERROR,
            )
