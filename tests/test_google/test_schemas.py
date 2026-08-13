from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from src.google.exceptions import InvalidGoogleOAuthCallbackState
from src.google.schemas import GmailInboxQuery, GmailMessageResponse, GoogleOAuth2StateCreate
from src.google.service.parser import parse_gmail_message
from src.schemas import PaginationQuery

from tests.test_google.constants import MOCK_AUTH_URL

class TestGoogleOAuth2StateCreate:

    # ===== GENERAL SCHEMA SHAPE =====
    def test_happy_schema_payload(self, happy_flow_payload: dict):
        assert GoogleOAuth2StateCreate(**happy_flow_payload).user_id == happy_flow_payload["user_id"]

    @pytest.mark.parametrize("missing_field", ["state", "auth_url", "user_id", "code_verifier"])
    def test_missing_field(self, missing_field: str, happy_flow_payload: dict):
        test_payload = {
            field: value
            for field, value in happy_flow_payload.items()
            if field != missing_field
        }

        with pytest.raises(ValidationError):
            GoogleOAuth2StateCreate(**test_payload)

    def test_extra_field(self, happy_flow_payload):
        test_payload = {**happy_flow_payload, "extra_field": "extra_value"}

        assert not hasattr(GoogleOAuth2StateCreate(**test_payload), "extra_field")

    # ===== TIMEZONE NORMALIZATION =====
    def test_happy_utc_normalization(self):
        happy_created_time = datetime(2026, 5, 11, 12, 0, tzinfo=UTC)

        assert GoogleOAuth2StateCreate.normalize_utc(happy_created_time) == happy_created_time
        assert happy_created_time.tzinfo is not None

    def test_non_utc_normalization(self):
        non_utc_created_time = datetime(2026, 5, 11, 12, 0)

        assert GoogleOAuth2StateCreate.normalize_utc(non_utc_created_time).tzinfo is not None

    # ===== AUTHORIZATION URL PARSING =====
    def test_valid_state_authurl(self):
        assert GoogleOAuth2StateCreate.auth_url_from_google(MOCK_AUTH_URL) == MOCK_AUTH_URL

    def test_state_authurl_wrong_domain(self):
        url = "https://wrong-domain.com/o/oauth2/auth?state=test-state&code_challenge=test-verifier"

        with pytest.raises(InvalidGoogleOAuthCallbackState):
            GoogleOAuth2StateCreate.auth_url_from_google(url)

    def test_state_authurl_missing_code(self):
        with pytest.raises(InvalidGoogleOAuthCallbackState):
            GoogleOAuth2StateCreate.auth_url_from_google(
                "https://accounts.google.com/o/oauth2/auth?state=test-state&code_verifier=test-verifier"
            )

    def test_state_authurl_missing_state(self):
        with pytest.raises(InvalidGoogleOAuthCallbackState):
            GoogleOAuth2StateCreate.auth_url_from_google(
                "https://accounts.google.com/o/oauth2/auth?code_challenge=test-challenge"
            )


class TestGmailInboxQuery:
    def test_to_gmail_query_serializes_filters(self):
        query = GmailInboxQuery(
            from_="sender@example.com",
            label="inbox",
            after=date(2026, 5, 1),
            before=date(2026, 5, 10),
        )

        assert (
            query.to_gmail_query()
            == "from:sender@example.com label:inbox after:2026-05-01 before:2026-05-10"
        )

    def test_to_gmail_query_returns_none_when_empty(self):
        assert GmailInboxQuery().to_gmail_query() is None

    def test_rejects_empty_text_filters(self):
        with pytest.raises(ValidationError):
            GmailInboxQuery(from_="   ")

    def test_rejects_text_filters_with_whitespace(self):
        with pytest.raises(ValidationError):
            GmailInboxQuery(label="my label")

    def test_accepts_valid_date_range(self):
        query = GmailInboxQuery(
            after=date(2026, 5, 1),
            before=date(2026, 5, 10),
        )

        assert query.after == date(2026, 5, 1)
        assert query.before == date(2026, 5, 10)

    def test_accepts_same_after_and_before_date(self):
        query = GmailInboxQuery(
            after=date(2026, 5, 1),
            before=date(2026, 5, 1),
        )

        assert query.after == query.before

    def test_rejects_after_later_than_before(self):
        with pytest.raises(ValidationError):
            GmailInboxQuery(
                after=date(2026, 5, 10),
                before=date(2026, 5, 1),
            )


class TestGmailMessageResponse:
    def test_validates_camelcase_gmail_metadata(self):
        message = GmailMessageResponse(
            **{
                "id": "19c0a050a6f77309",
                "threadId": "19c0a050a6f77309",
                "subject": "Update to our Terms of Use and Privacy Policy",
                "sender": "Ubisoft <news@updates.ubisoft.com>",
                "to": "<LILMISSMJ.0606@gmail.com>",
                "cc": None,
                "body": "Hello,\r\n\r\nWe are updating Ubisoft's Terms of Use.",
                "receiveTime": "Thu, 29 Jan 2026 07:50:26 -0600",
                "internalDate": "2026-01-29T13:50:26Z",
                "labelIds": ["CATEGORY_UPDATES", "INBOX", "Label_123"],
            }
        )

        assert not hasattr(message, "id")
        assert not hasattr(message, "thread_id")
        assert message.sender == "news@updates.ubisoft.com"
        assert message.to == "LILMISSMJ.0606@gmail.com"
        assert not hasattr(message, "date")
        assert message.receive_time == "Thu, 29 Jan 2026 07:50:26 -0600"
        assert not hasattr(message, "internal_date")
        assert message.label_ids == ["CATEGORY_UPDATES", "INBOX", "Label_123"]

    def test_validates_parsed_gmail_message(self):
        parsed_message = parse_gmail_message(
            {
                "id": "message-id",
                "threadId": "thread-id",
                "internalDate": "1777776002000",
                "labelIds": ["INBOX"],
                "payload": {
                    "mimeType": "text/plain",
                    "headers": [
                        {"name": "Subject", "value": "Subject line"},
                        {"name": "From", "value": "sender@example.com"},
                        {"name": "To", "value": "merchant@example.com"},
                        {"name": "Date", "value": "Sun, 03 May 2026 09:15:00 +0000"},
                    ],
                    "body": {"data": "SGVsbG8="},
                },
            }
        )
        message = GmailMessageResponse(**parsed_message)

        assert "id" not in parsed_message
        assert "thread_id" not in parsed_message
        assert message.subject == "Subject line"
        assert message.sender == "sender@example.com"
        assert message.to == "merchant@example.com"
        assert message.body == "Hello"
        assert "date" not in parsed_message
        assert "date_header" not in parsed_message
        assert "internal_date" not in parsed_message
        assert message.receive_time == "Sun, 03 May 2026 09:15:00 +0000"
        assert message.label_ids == ["INBOX"]

    def test_validates_parsed_html_gmail_message(self):
        parsed_message = parse_gmail_message(
            {
                "id": "message-id",
                "payload": {
                    "mimeType": "text/html",
                    "headers": [],
                    "body": {"data": "PGRpdj5IZWxsbyA8c3Ryb25nPlN0YW48L3N0cm9uZz48L2Rpdj4="},
                },
            }
        )
        message = GmailMessageResponse(**parsed_message)

        assert message.body == "Hello\nStan"

    @pytest.mark.parametrize(
        "payload",
        [
            {"receiveTime": "x" * 999},
            {"sender": "not-an-email-address"},
            {"labelIds": [""]},
        ],
    )
    def test_rejects_invalid_metadata(self, payload):
        with pytest.raises(ValidationError):
            GmailMessageResponse(**payload)


class TestPaginationQuery:
    def test_defaults(self):
        query = PaginationQuery()

        assert query.offset == 0
        assert query.limit == 5

    @pytest.mark.parametrize(
        "payload",
        [
            {"offset": -1},
            {"limit": 0},
            {"limit": 101},
        ],
    )
    def test_rejects_invalid_values(self, payload):
        with pytest.raises(ValidationError):
            PaginationQuery(**payload)
