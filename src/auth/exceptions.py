from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.exceptions import BaseExceptionHandler


# =============== DOMAIN-SPECIFIC EXCEPTIONS ===============
class UsernameAlreadyExists(Exception):
    pass


class InvalidFormData(Exception):
    pass


class UnauthenticatedUser(Exception):
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
    """API-only handler — see BaseExceptionHandler for why the SSR branch was dropped."""

    def register_exception_handlers(self) -> None:
        @self.app.exception_handler(InvalidFormData)
        async def invalid_form_data_handler(request: Request, _exc: InvalidFormData):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid form data."},
            )

        @self.app.exception_handler(UsernameAlreadyExists)
        async def username_already_exists_handler(
            request: Request, _exc: UsernameAlreadyExists
        ):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": "Username already exists."},
            )

        @self.app.exception_handler(UnauthenticatedUser)
        async def unauthenticated_user_handler(
            request: Request, _exc: UnauthenticatedUser
        ):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Unauthenticated. Incorrect username or password."},
                headers={"WWW-Authenticate": "Bearer"},
            )

        @self.app.exception_handler(MalformedToken)
        async def malformed_token_handler(request: Request, _exc: MalformedToken):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": "Malformed access_token. Please log in and try again."
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        @self.app.exception_handler(UserNotFound)
        async def user_not_found_handler(request: Request, _exc: UserNotFound):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "User not found."},
            )

        @self.app.exception_handler(AlreadyAuthenticated)
        async def already_authenticated_handler(
            request: Request, _exc: AlreadyAuthenticated
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Already authenticated."},
            )

        @self.app.exception_handler(InsufficientPermission)
        async def insufficient_permission_handler(
            request: Request, _exc: InsufficientPermission
        ):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Insufficient permissions"},
            )
