from datetime import date

from pydantic import EmailStr, Field

from src.schemas import CustomBaseModel


class OrderParseRequest(CustomBaseModel):
    body: str = Field(..., min_length=1, description="Raw email body content to parse.")


class OrderResponse(CustomBaseModel):
    merchant_id: int = Field(..., description="Application user id that owns this order.")
    order_number: str = Field(..., description="Provider order reference.")
    order_date: date | None = Field(default=None, description="Scheduled delivery date.")
    full_name: str | None = Field(default=None, description="Customer full name.")
    is_cancel: bool | None = Field(default=None, description="Whether the order appears cancelled.")
    office_email: EmailStr | None = Field(default=None, description="Customer office email.")
    private_email: EmailStr | None = Field(default=None, description="Customer private email.")
    treatment_selected: str | None = Field(default=None, description="Selected treatment.")
    location: str | None = Field(default=None, description="Selected location.")


class ParsedOrderResponse(CustomBaseModel):
    order: OrderResponse
    message: str = Field(default="Order parsed successfully.")


class OrdersListResponse(CustomBaseModel):
    orders: list[OrderResponse]
    result_size_estimate: int | None = Field(default=None)


class OrdersFetchResponse(CustomBaseModel):
    persisted_count: int = Field(..., ge=0, description="Number of orders persisted to the database.")
    debug_message: str = Field(..., min_length=1, description="Debug-oriented status message.")
