"""Self-contained Jinja setup for this domain's one HTML artifact: the reminder
email. The source project rendered this (and a template-preview page) through a
shared, app-wide SSR templating layer; that layer isn't part of this extraction
(see README), so `notification` owns its own tiny Jinja environment instead of
reaching into another domain for it.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

notification_email_template = _env.get_template("reminder_email.html")
