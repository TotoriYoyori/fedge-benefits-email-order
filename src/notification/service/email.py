import base64
from pathlib import Path

from src.notification.schemas import EmailSendRequest
from src.notification.templating import notification_email_template

# --------------- EXAMPLE BUSINESS IDENTITY ---------------
BUSINESS_NAME = "the wellness studio"
BUSINESS_WEBSITE = "https://example-wellness-studio.test"
BUSINESS_WEBSITE_LABEL = "www.example-wellness-studio.test"
BUSINESS_PHONE = "+46 40 000 000"
BUSINESS_ADDRESSES: dict[str, str] = {
    "Malmö": "Studiogatan 12, 211 34 Malmö",
    "Helsingborg": "Studiogatan 4, 252 20 Helsingborg",
}
BOOKING_LINKS: dict[str, str] = {
    "Malmö": "https://example-booking.test/locations/malmo",
    "Helsingborg": "https://example-booking.test/locations/helsingborg",
}
DEFAULT_BOOKING_LINK = "https://example-booking.test/locations"


def _booking_link_for(location: str) -> str:
    return BOOKING_LINKS.get(location, DEFAULT_BOOKING_LINK)


# --------------- EMAIL BANNER ASSET ---------------
# Inlined as a base64 data URI so the rendered email is fully self-contained
# and doesn't depend on an externally-hosted image (which the recipient's
# mail client may block or which may go stale).
_BANNER_PATH = Path(__file__).resolve().parent.parent / "templates" / "assets" / "banner.jpg"


def _banner_data_uri() -> str:
    encoded = base64.b64encode(_BANNER_PATH.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


BANNER_DATA_URI = _banner_data_uri()


# =============== TEXT BODY TEMPLATE ===============
EMAIL_PLAINTEXT_TEMPLATE = (
    "Hej{greeting_name}!\n\n"
    "En liten paminnelse att boka din behandling.\n\n"
    "Du har tidigare bestallt {treatment} hos oss pa " + BUSINESS_NAME + " "
    "med ditt friskvardsbidrag, men har annu inte bokat din tid.\n\n"
    "Klicka och boka din tid for {location}:\n"
    "{booking_link}\n\n"
    "Med vanliga halsningar,\n\n"
    "Om du redan har bokat hos oss, ignorera garna detta meddelande."
    "{order_number_line}\n\n"
    "(c) " + BUSINESS_NAME
)


# =============== DRAFTING MESSAGE FUNCTIONS ===============
def write_email_html(send_request: EmailSendRequest) -> str:
    return notification_email_template.render(
        name=send_request.name.strip().split()[0] if send_request.name else "",
        treatment=send_request.treatment,
        location=send_request.location,
        order_number=send_request.order_number,
        booking_link=_booking_link_for(send_request.location),
        malmo_booking_link=BOOKING_LINKS["Malmö"],
        helsingborg_booking_link=BOOKING_LINKS["Helsingborg"],
        malmo_address=BUSINESS_ADDRESSES["Malmö"],
        helsingborg_address=BUSINESS_ADDRESSES["Helsingborg"],
        business_name=BUSINESS_NAME,
        business_website=BUSINESS_WEBSITE,
        business_website_label=BUSINESS_WEBSITE_LABEL,
        business_phone=BUSINESS_PHONE,
        banner_data_uri=BANNER_DATA_URI,
    )


def write_email_plaintext(send_request: EmailSendRequest) -> str:
    greeting_name = f" {send_request.name}" if send_request.name else ""
    order_number_line = (
        f"\nOrdernummer: {send_request.order_number}"
        if send_request.order_number
        else ""
    )

    return EMAIL_PLAINTEXT_TEMPLATE.format(
        greeting_name=greeting_name,
        treatment=send_request.treatment,
        location=send_request.location,
        booking_link=_booking_link_for(send_request.location),
        order_number_line=order_number_line,
    )
