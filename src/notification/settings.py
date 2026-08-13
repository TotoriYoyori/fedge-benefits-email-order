from typing import Optional

from pydantic import EmailStr, model_validator

from src.notification.schemas import EmailProviderName
from src.schemas import DomainSettings

# =============== SETTINGS ===============
class NotificationSettings(DomainSettings):
    # ===== Global App
    EMAIL_PROVIDER: EmailProviderName
    EMAIL_FROM_NAME: str
    EMAIL_FROM_ADDRESS: EmailStr
    # ===== Resend-specific settings
    RESEND_API_KEY: Optional[str] = None
    # ===== Mailtrap-specific settings
    MAILTRAP_API_KEY: Optional[str] = None
    MAILTRAP_SANDBOX_INBOX_ID: Optional[int] = None

    @model_validator(mode="after")
    def validate_provider_settings(self) -> "NotificationSettings":
        if self.EMAIL_PROVIDER == EmailProviderName.RESEND and not self.RESEND_API_KEY:
            raise ValueError("RESEND_API_KEY is required when EMAIL_PROVIDER is resend.")

        if self.EMAIL_PROVIDER == EmailProviderName.MAILTRAP and (
            not self.MAILTRAP_API_KEY or not self.MAILTRAP_SANDBOX_INBOX_ID
        ):
            raise ValueError(
                "MAILTRAP_API_KEY and MAILTRAP_SANDBOX_INBOX_ID are required " "when EMAIL_PROVIDER is mailtrap."
            )

        return self

    @property
    def email_from(self) -> str:
        return f"{self.EMAIL_FROM_NAME} <{self.EMAIL_FROM_ADDRESS}>"


# =============== APP INSTANCE ===============
notification_settings = NotificationSettings()
