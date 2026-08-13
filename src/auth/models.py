from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


# =============== AUTH DOMAIN MODELS ===============
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="user")
    registration_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    google_oauth_states: Mapped[list["GoogleOAuthState"]] = relationship(
        back_populates="user"
    )
    google_oauth_credential: Mapped["GoogleOAuthCredential | None"] = relationship(
        back_populates="user",
        uselist=False,
    )

    def __str__(self) -> str:
        return f"Username: {self.username} | Email: {self.email} {type(self)}"

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, username={self.username!r}, "
            f"email={self.email!r}, role={self.role!r})"
        )
