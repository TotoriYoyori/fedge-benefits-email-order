from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from src.auth.models import User
from src.google.dependencies import (
    valid_google_oauth2_state,
    valid_google_oauth_credential,
)
from src.google.models import GoogleOAuthCredential, GoogleOAuthState
from src.google.schemas import GoogleOAuth2StateCreate


# =============== MODEL FIXTURES ===============
@pytest.fixture
def fake_db():
    return object()


@pytest.fixture
def valid_user() -> User:
    return User(
        id=1,
        username="merchant_user",
        email="merchant@example.com",
        password_hash="hashed-password",
        role="merchant",
        registration_time=datetime.now(UTC),
    )


# =============== OAUTH2 STATE FIXTURES ===============
@pytest.fixture
def happy_flow_payload() -> dict:
    return {
        "state": "abc123state",
        "auth_url": "https://accounts.google.com/o/oauth2/auth?state=abc123state&code_challenge=test-challenge",
        "user_id": 42,
        "code_verifier": "pkce-code-verifier-value",
    }


@pytest.fixture
def state_create(happy_flow_payload):
    return GoogleOAuth2StateCreate(**happy_flow_payload)


@pytest.fixture
def oauth_state(state_create):
    return GoogleOAuthState(**state_create.model_dump())


# =============== OAUTH2 STATE FIXTURES ===============
@pytest.fixture
def oauth_credential():
    return GoogleOAuthCredential(
        id=1,
        user_id=1,
        access_token="access-token",
        refresh_token="refresh-token",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="client-id",
        client_secret="client-secret",
        scopes="openid,email,https://www.googleapis.com/auth/gmail.readonly",
        expiry=datetime.now(UTC),
        email_address="merchant@example.com",
        created_time=datetime.now(UTC),
        updated_time=datetime.now(UTC),
    )


# =============== SERVICE MOCK FIXTURES ===============
@pytest.fixture
def mock_initiate_oauth2(oauth_state):
    with patch("src.google.router.initiate_oauth2") as mock:
        mock.return_value = oauth_state
        yield mock


@pytest.fixture
def mock_exchange_code_for_credentials():
    with patch("src.google.router.exchange_code_for_credentials") as mock:
        mock.return_value = GoogleOAuthCredential(
            id=1,
            user_id=1,
            access_token="access-token",
            refresh_token="refresh-token",
            token_uri="https://oauth2.googleapis.com/token",
            client_id="client-id",
            client_secret="client-secret",
            scopes="openid,email,https://www.googleapis.com/auth/gmail.readonly",
            expiry=datetime.now(UTC),
            email_address="merchant@example.com",
            created_time=datetime.now(UTC),
            updated_time=datetime.now(UTC),
        )
        yield mock


@pytest.fixture
def mock_connect_gmail_service(oauth_credential):
    with patch("src.google.router.connect_gmail_service") as mock:
        mock.return_value = oauth_credential
        yield mock


# =============== DEPENDENCY OVERRIDE FIXTURES ===============
@pytest.fixture
def override_valid_google_oauth2_state(oauth_state, override_dependency):
    return override_dependency(valid_google_oauth2_state, oauth_state)


@pytest.fixture
def override_valid_google_oauth_credential(oauth_credential, override_dependency):
    return override_dependency(valid_google_oauth_credential, oauth_credential)
