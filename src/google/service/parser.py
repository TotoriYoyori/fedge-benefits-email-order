from base64 import urlsafe_b64decode

from bs4 import BeautifulSoup


class GmailMessageParser:
    def __init__(self, message: dict) -> None:
        self._message = message
        self._payload = message.get("payload", {})
        self._headers = self._extract_headers()

    def parse(self) -> dict:
        return {
            "subject": self._headers.get("subject"),
            "sender": self._headers.get("from"),
            "to": self._headers.get("to"),
            "cc": self._headers.get("cc"),
            "body": self._extract_body_text(),
            "receive_time": self._headers.get("date"),
            "label_ids": self._message.get("labelIds") or [],
        }

    def _extract_headers(self) -> dict[str, str]:
        return {
            header["name"].lower(): header["value"]
            for header in self._payload.get("headers", [])
            if header.get("name") and header.get("value")
        }

    def _extract_body_text(self) -> str | None:
        plain_text = self._find_body_by_mime_type(self._payload, "text/plain")
        if plain_text:
            return plain_text

        html_text = self._find_body_by_mime_type(self._payload, "text/html")
        if html_text:
            return self._strip_html(html_text)

        return self._decode_body_data(self._payload.get("body", {}).get("data"))

    def _find_body_by_mime_type(self, payload: dict, mime_type: str) -> str | None:
        if payload.get("mimeType") == mime_type:
            decoded = self._decode_body_data(payload.get("body", {}).get("data"))
            if decoded:
                return decoded

        for part in payload.get("parts", []):
            decoded = self._find_body_by_mime_type(part, mime_type)
            if decoded:
                return decoded

        return None

    @staticmethod
    def _decode_body_data(body_data: str | None) -> str | None:
        if not body_data:
            return None

        padding = "=" * (-len(body_data) % 4)
        try:
            decoded_bytes = urlsafe_b64decode(f"{body_data}{padding}")
        except (ValueError, TypeError):
            return None

        try:
            return decoded_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return decoded_bytes.decode("latin-1", errors="replace")

    @staticmethod
    def _strip_html(html_content: str) -> str:
        return BeautifulSoup(html_content, "html.parser").get_text("\n", strip=True)


# =============== PUBLIC API CALLS ===============
def parse_gmail_message(message: dict) -> dict:
    return GmailMessageParser(message).parse()
