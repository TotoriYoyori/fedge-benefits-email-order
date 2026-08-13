import csv
import io
from datetime import date

from googleapiclient.discovery import Resource
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.google.schemas import GmailInboxQuery
from src.google.service import get_gmail_messages
from src.orders.models import Orders
from src.orders.parsers import OrdersParser
from src.schemas import PaginationQuery


BENIFY_SENDER = "fps@benify.com"


async def list_benify_orders(
    gmail_service: Resource,
    merchant_id: int,
    max_results: int,
    label: str | None = None,
    after: date | None = None,
    before: date | None = None,
) -> dict:
    inbox_response = await get_gmail_messages(
        service=gmail_service,
        pagination=PaginationQuery(limit=max_results),
        query=GmailInboxQuery(
            from_=BENIFY_SENDER,
            label=label,
            after=after,
            before=before,
        ),
    )
    parsed_orders = _parse_orders_from_inbox(
        messages=inbox_response.get("messages", []),
        merchant_id=merchant_id,
    )

    return {
        "orders": parsed_orders,
        "result_size_estimate": inbox_response.get("result_size_estimate"),
    }


async def fetch_and_persist_benify_orders(
    db: AsyncSession,
    gmail_service: Resource,
    merchant_id: int,
    max_results: int,
    label: str | None = None,
    after: date | None = None,
    before: date | None = None,
) -> dict:
    parsed_orders_response = await list_benify_orders(
        gmail_service=gmail_service,
        merchant_id=merchant_id,
        max_results=max_results,
        label=label,
        after=after,
        before=before,
    )
    parsed_orders = parsed_orders_response["orders"]
    persisted_count = await _upsert_orders(db, parsed_orders)

    return {
        "persisted_count": persisted_count,
        "debug_message": (
            f"Fetched {len(parsed_orders)} Benify orders and persisted "
            f"{persisted_count} rows for merchant_id={merchant_id}."
        ),
    }


async def list_persisted_orders(
    db: AsyncSession,
    merchant_id: int,
) -> dict:
    stmt = (
        select(Orders)
        .where(Orders.merchant_id == merchant_id)
        .order_by(Orders.order_date.desc(), Orders.order_number.desc())
    )
    result = await db.execute(stmt)
    orders = list(result.scalars().all())

    return {
        "orders": orders,
        "result_size_estimate": len(orders),
    }


CSV_COLUMNS = (
    "date",
    "full_name",
    "order_number",
    "is_cancel",
    "office_email",
    "private_email",
    "treatment_selected",
    "location",
)


async def export_orders_csv(db: AsyncSession, merchant_id: int) -> str:
    """Export a merchant's persisted orders as CSV text.

    This is the "view it as csv" half of the pipeline's premise — the source
    project did this ad hoc (a manual export used to cross-reference which
    customers needed a reminder); this is that same shape as a real, tested
    endpoint instead of a one-off script.
    """
    listing = await list_persisted_orders(db=db, merchant_id=merchant_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)

    for order in listing["orders"]:
        writer.writerow(
            [
                order.order_date.isoformat() if order.order_date else "",
                order.full_name or "",
                order.order_number,
                order.is_cancel if order.is_cancel is not None else "",
                order.office_email or "",
                order.private_email or "",
                order.treatment_selected or "",
                order.location or "",
            ]
        )

    return buffer.getvalue()


def _parse_orders_from_inbox(messages: list[dict], merchant_id: int) -> list[Orders]:
    parsed_orders: list[Orders] = []

    for message in messages:
        body = message.get("body")
        if not body:
            continue

        try:
            parsed_orders.append(
                OrdersParser.parse_body(body, merchant_id=merchant_id)
            )
        except ValueError:
            continue

    return parsed_orders


async def _upsert_orders(db: AsyncSession, orders: list[Orders]) -> int:
    persisted_count = 0

    for parsed_order in orders:
        existing_order = await db.get(Orders, parsed_order.order_number)

        if existing_order is None:
            db.add(parsed_order)
            persisted_count += 1
            continue

        existing_order.merchant_id = parsed_order.merchant_id
        existing_order.order_date = parsed_order.order_date
        existing_order.full_name = parsed_order.full_name
        existing_order.is_cancel = parsed_order.is_cancel
        existing_order.office_email = parsed_order.office_email
        existing_order.private_email = parsed_order.private_email
        existing_order.treatment_selected = parsed_order.treatment_selected
        existing_order.location = parsed_order.location
        persisted_count += 1

    await db.commit()
    return persisted_count
