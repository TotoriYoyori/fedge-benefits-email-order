from pathlib import Path
from typing import Annotated

from fastapi import Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel, to_pascal
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============== API RESPONSE SCHEMAS BASE INHERITANCE ===============
class CustomBaseModel(BaseModel):
    """
    Base model with shared configuration for all project schemas.

    Features:
        - CamelCase alias generation for JSON fields.
        - Allows population by original Python field names.
        - Supports initialization from object attributes.

    Example:
        >>> class APIResponse(CustomBaseModel):
        ...     first_name: str
    """

    model_config = SettingsConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class QueryModel(BaseModel):
    """
    Base Model with shared configuration for query parameters.

    Features:
        - Alias generation with hyphenated field names (kebab-case).
        - Forbid extra fields in the model.
        - Populate by original Python field names.
    """
    model_config = SettingsConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# =============== OFFSET AND LIMIT SHARED QUERY PATTERN ===============
class PaginationQuery(QueryModel):
    offset: Annotated[int, Query(ge=0)] = 0
    limit: Annotated[int, Query(ge=1, le=100)] = 5


# =============== MODULE CONFIGURATION BASE CLASS ===============
class DomainSettings(BaseSettings):
    """
    Base settings class for domain-level configuration.

    Loads values from environment variables and a shared `.env` file,
    as well as compile all static and templates path for the entire project.

    Attributes:
        ENVIRONMENT (str): Current runtime environment (e.g., local, dev, prod).
        TEMPLATES_DIR (str): Path to the templates' directory.
        STATIC_DIR (str): Path to the static files' directory.
        DEFAULT_TEMPLATE_NAME (str): Default template filename.

    Example:
        >>> class AuthSettings(DomainSettings):
        >>>     SECRET_KEY: SecretStr
        >>>     ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
        >>> assert AuthSettings.DEFAULT_TEMPLATE_NAME == "index.html"
    """

    ENVIRONMENT: str = "local"
    TEMPLATES_DIR: str = ""
    STATIC_DIR: str = ""
    DEFAULT_TEMPLATE_NAME: str = "index.html"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    def model_post_init(self, __context):
        import sys

        module = sys.modules[self.__class__.__module__]
        domain_path = Path(module.__file__).resolve().parent

        object.__setattr__(self, "TEMPLATES_DIR", str(domain_path / "templates"))
        object.__setattr__(self, "STATIC_DIR", str(domain_path / "static"))


# --------------- REUSABLE API ROUTE CONFIGURATIONS
class RouteDecoratorPreset:
    """
    Provide reusable FastAPI route configuration presets for responses.

    Available presets:
        - html_get(): Preset for GET routes returning HTML.
        - html_post(): Preset for POST routes returning HTML.

    Example:
        >>> preset = RouteDecoratorPreset.html_get()
        >>> preset["status_code"]
        200
    """

    @staticmethod
    def html_get() -> dict:
        return {
            "response_model": None,
            "response_class": HTMLResponse,
            "status_code": status.HTTP_200_OK,
            "responses": {
                200: {"description": "HTML template rendered successfully"},
                404: {"description": "HTML template rendered failed"},
            },
        }

    @staticmethod
    def html_post() -> dict:
        return {
            "response_model": None,
            "response_class": HTMLResponse,
            "status_code": status.HTTP_200_OK,
            "responses": {
                200: {"description": "HTML template rendered successfully"},
            },
        }
