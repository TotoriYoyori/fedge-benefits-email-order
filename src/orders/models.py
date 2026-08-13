from datetime import date

from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Orders(Base):
    __tablename__ = "orders"

    merchant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    order_number: Mapped[str] = mapped_column(String(255), primary_key=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_cancel: Mapped[bool] = mapped_column(Boolean, nullable=True)
    office_email: Mapped[str] = mapped_column(String(255), nullable=True)
    private_email: Mapped[str] = mapped_column(String(255), nullable=True)
    treatment_selected: Mapped[str] = mapped_column(String(255), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)

    def __str__(self) -> str:
        return (
            f"Order [{self.order_number}] for merchant [{self.merchant_id}]: "
            f"{self.full_name} ({self.office_email}) for {self.treatment_selected} at {self.location} "
            f"{type(self)}"
        )

    def __repr__(self) -> str:
        return (
            f"Orders(order_number={self.order_number!r}, full_name={self.full_name!r})"
        )
