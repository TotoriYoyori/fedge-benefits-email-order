from pydantic import SecretStr

from src.schemas import DomainSettings


# =============== AUTH MODULE CONFIGURATION ===============
class AuthSettings(DomainSettings):
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DEV_ROLE_KEYS: str = "{}"


# =============== SHARED AUTHENTICATION SETTINGS ===============
auth_settings = AuthSettings()
