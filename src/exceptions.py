from abc import ABC, abstractmethod

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class BaseExceptionHandler(ABC):
    """Shared exception handler utilities. Domain handlers inherit and extend this.

    Note: this is a trimmed, API-only version of the original handler. The source
    project also rendered browser-facing HTML error pages via a shared SSR template
    layer; that layer isn't part of this extraction, so every handler here returns
    JSON only.
    """

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
