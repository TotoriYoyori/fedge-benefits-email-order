from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.exceptions import BaseExceptionHandler, GENERIC_VALIDATION_ERROR

GENERIC_NOT_FOUND_ERROR = {"detail": "Not found."}


# =============== DOMAIN-SPECIFIC EXCEPTIONS ===============
class UsernameAlreadyExists(Exception):
    """A username was already taken at registration."""
    pass


class InvalidFormData(Exception):
    pass


class InvalidCredentials(Exception):
    """A /login attempt's username/password did not match."""
    pass


class UnauthenticatedUser(Exception):
    """No bearer token was supplied on a route that requires one."""
    pass


class MalformedToken(Exception):
    pass


class UserNotFound(Exception):
    pass


class AlreadyAuthenticated(Exception):
    pass


class InsufficientPermission(Exception):
    pass


# =============== FASTAPI EXCEPTION HANDLERS ===============
class AuthExceptionHandler(BaseExceptionHandler):

    def register_exception_handlers(self) -> None:
        # ----- /register, /login (authentication)
        @self.app.exception_handler(InvalidFormData)
        @self.app.exception_handler(UsernameAlreadyExists)
        @self.app.exception_handler(InvalidCredentials)
        @self.app.exception_handler(AlreadyAuthenticated)
        async def validation_style_handler(request: Request, _exc: Exception):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content=GENERIC_VALIDATION_ERROR,
            )

        # ----- any bearer-token/role-gated route (authorization)
        @self.app.exception_handler(UnauthenticatedUser)
        @self.app.exception_handler(MalformedToken)
        @self.app.exception_handler(UserNotFound)
        @self.app.exception_handler(InsufficientPermission)
        async def not_found_style_handler(request: Request, _exc: Exception):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=GENERIC_NOT_FOUND_ERROR,
            )
