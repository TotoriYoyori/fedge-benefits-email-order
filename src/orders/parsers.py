import re
from datetime import date

from src.orders.models import Orders


class OrdersParser:
    @staticmethod
    def normalize_body(body: str) -> str:
        return body.replace("\r\n", "\n").replace("\r", "\n").strip()

    @staticmethod
    def extract_order_number(body: str) -> str:
        match = re.search(r"Your order number:\s*([^\n]+)", body)
        if not match:
            raise ValueError("Order number could not be parsed from email body.")

        return match.group(1).strip()

    @staticmethod
    def extract_full_name(body: str) -> str | None:
        first_name = OrdersParser.extract_tabbed_value(body, "First name")
        surname = OrdersParser.extract_tabbed_value(body, "Surname")

        if first_name and surname:
            return f"{first_name} {surname}".strip()
        if first_name:
            return first_name
        if surname:
            return surname

        match = re.search(r"([^\n]+?)\s+has ordered\s+\"", body)
        if match:
            return match.group(1).strip()

        return None

    @staticmethod
    def extract_order_date(body: str) -> date | None:
        match = re.search(r"for delivery on (\d{4}-\d{2}-\d{2})", body)
        if not match:
            return None

        return date.fromisoformat(match.group(1))

    @staticmethod
    def extract_is_cancel(body: str) -> bool:
        lowered = body.lower()
        return " has been cancelled" in lowered or " is cancelled" in lowered

    @staticmethod
    def extract_office_email(body: str) -> str | None:
        return OrdersParser.extract_tabbed_value(body, "Office email")

    @staticmethod
    def extract_private_email(body: str) -> str | None:
        return OrdersParser.extract_tabbed_value(body, "Private email")

    @staticmethod
    def extract_treatment_selected(body: str) -> str | None:
        match = re.search(r"Select treatment:\s*(.+?)(?:\t[^\n]+)?\n", body)
        if match:
            return match.group(1).strip()

        return None

    @staticmethod
    def extract_location(body: str) -> str | None:
        return OrdersParser.extract_tabbed_value(body, "Choose location")

    @staticmethod
    def extract_tabbed_value(body: str, label: str) -> str | None:
        pattern = rf"{re.escape(label)}\t([^\t\n]+)"
        match = re.search(pattern, body)
        if not match:
            return None

        value = match.group(1).strip()
        return value or None

    @staticmethod
    def parse_body(body: str, merchant_id: int) -> Orders:
        normalized_body = OrdersParser.normalize_body(body)

        return Orders(
            merchant_id=merchant_id,
            order_number=OrdersParser.extract_order_number(normalized_body),
            order_date=OrdersParser.extract_order_date(normalized_body),
            full_name=OrdersParser.extract_full_name(normalized_body),
            is_cancel=OrdersParser.extract_is_cancel(normalized_body),
            office_email=OrdersParser.extract_office_email(normalized_body),
            private_email=OrdersParser.extract_private_email(normalized_body),
            treatment_selected=OrdersParser.extract_treatment_selected(normalized_body),
            location=OrdersParser.extract_location(normalized_body),
        )
