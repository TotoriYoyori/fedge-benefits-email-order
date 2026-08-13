from datetime import datetime, UTC

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from src.database import Base
from src.auth.models import User

# =============== STATE MODEL ===============
class UTCDateTime(TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_result_value(self, value: datetime, dialect) -> datetime:
        """Called when reading a value from the DB."""
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)


class GoogleOAuthState(Base):
    __tablename__ = "google_oauth_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    auth_url: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    code_verifier: Mapped[str] = mapped_column(Text, nullable=False)
    created_time: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    user: Mapped["User"] = relationship(back_populates="google_oauth_states")


# =============== CREDENTIAL MODEL ===============
class GoogleOAuthCredential(Base):
    __tablename__ = "google_oauth_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_uri: Mapped[str] = mapped_column(String(255), nullable=False)
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    client_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False)
    expiry: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    email_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_time: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    updated_time: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)

    user: Mapped["User"] = relationship(back_populates="google_oauth_credential")
