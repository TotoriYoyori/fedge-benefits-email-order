from pathlib import Path
from typing import Any

from src.schemas import DomainSettings


# =============== DOMAIN SETTINGS ===============
class GoogleSettings(DomainSettings):
    """Domain settings for Google OAuth and Gmail integration."""

    # ----- Google OAuth General Settings
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:8000/api/v1/google/callback"
    GOOGLE_SCOPES: str = "openid,email,https://www.googleapis.com/auth/gmail.readonly"
    GOOGLE_CLIENT_SECRETS_FILE: str = ""
    GOOGLE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    GOOGLE_AUTH_PROVIDER_CERT_URL: str = "https://www.googleapis.com/oauth2/v1/certs"

    # ----- Flow Generation Settings
    FLOW_ACCESS_TYPE: str = "offline"
    FLOW_INCLUDE_GRANTED_SCOPES: str = "true"
    FLOW_PROMPT: str = "consent"
    FLOW_STATE_TTL_MINUTES: int = 10

    def model_post_init(self, __context):
        """
        Sets `GOOGLE_CLIENT_SECRETS_FILE` to the domain-local `credentials.json` file.

        Callers may still avoid this file by configuring `GOOGLE_CLIENT_ID` and
        `GOOGLE_CLIENT_SECRET` through environment variables.
        """
        super().model_post_init(__context)
        object.__setattr__(
            self,
            "GOOGLE_CLIENT_SECRETS_FILE",
            str(Path(__file__).resolve().parent / "credentials.json"),
        )

    @property
    def has_env_client_config(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    def oauth_client_config(self) -> dict[str, dict[str, Any]]:
        return {
            "installed": {
                "client_id": self.GOOGLE_CLIENT_ID,
                "client_secret": self.GOOGLE_CLIENT_SECRET,
                "auth_uri": self.GOOGLE_AUTH_URI,
                "token_uri": self.GOOGLE_TOKEN_URI,
                "auth_provider_x509_cert_url": self.GOOGLE_AUTH_PROVIDER_CERT_URL,
                "redirect_uris": [self.GOOGLE_REDIRECT_URI],
            }
        }


# =============== SHARED SETTINGS ===============
google_settings = GoogleSettings()
