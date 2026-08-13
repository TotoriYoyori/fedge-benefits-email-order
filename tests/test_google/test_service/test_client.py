from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from src.google.service import state_is_stale
from src.google.schemas import GoogleOAuth2CredentialCreate
from src.google.service.client import (
    _fetch_base_flow,
    fetch_refreshed_google_oauth_credential,
)

class TestStateIsStale:
    def test_true_for_expired_state(self, oauth_state) -> None:
        oauth_state.created_time = oauth_state.created_time - timedelta(hours=24)

        assert state_is_stale(oauth_state) is True

    def test_false_for_fresh_state(self, oauth_state) -> None:
        assert state_is_stale(oauth_state) is False


class TestFetchBaseFlow:
    def test_uses_env_client_config_when_available(self):
        settings = SimpleNamespace(
            has_env_client_config=True,
            oauth_client_config=lambda: {"installed": {"client_id": "client-id"}},
            GOOGLE_SCOPES="openid,email",
            GOOGLE_REDIRECT_URI="http://127.0.0.1:8000/api/v1/google/callback",
            GOOGLE_CLIENT_SECRETS_FILE="unused.json",
        )

        with (
            patch("src.google.service.client.google_settings", settings),
            patch("src.google.service.client.Flow.from_client_config") as from_client_config,
            patch("src.google.service.client.Flow.from_client_secrets_file") as from_client_secrets_file,
        ):
            result = _fetch_base_flow()

        assert result == from_client_config.return_value
        from_client_config.assert_called_once_with(
            {"installed": {"client_id": "client-id"}},
            scopes=["openid", "email"],
            redirect_uri="http://127.0.0.1:8000/api/v1/google/callback",
        )
        from_client_secrets_file.assert_not_called()

    def test_falls_back_to_client_secrets_file_when_env_config_is_missing(self):
        settings = SimpleNamespace(
            has_env_client_config=False,
            GOOGLE_SCOPES="openid,email",
            GOOGLE_REDIRECT_URI="http://127.0.0.1:8000/api/v1/google/callback",
            GOOGLE_CLIENT_SECRETS_FILE="credentials.json",
        )

        with (
            patch("src.google.service.client.google_settings", settings),
            patch("src.google.service.client.Flow.from_client_secrets_file") as from_client_secrets_file,
        ):
            result = _fetch_base_flow()

        assert result == from_client_secrets_file.return_value
        from_client_secrets_file.assert_called_once_with(
            "credentials.json",
            scopes=["openid", "email"],
            redirect_uri="http://127.0.0.1:8000/api/v1/google/callback",
        )


class TestFetchRefreshedGoogleOauthCredential:
    async def test_fresh_credential_returns_existing_credential_payload(
        self,
        oauth_credential,
    ) -> None:
        credentials = Mock()
        credentials.expired = False

        with (
            patch(
                "src.google.service.client._convert_to_google_credential",
                return_value=credentials,
            ),
            patch("src.google.service.client.asyncer.asyncify") as asyncify,
        ):
            result = await fetch_refreshed_google_oauth_credential(oauth_credential)

        assert isinstance(result, GoogleOAuth2CredentialCreate)
        assert result.user_id == oauth_credential.user_id
        assert result.access_token == oauth_credential.access_token
        assert result.refresh_token == oauth_credential.refresh_token
        assert result.token_uri == oauth_credential.token_uri
        assert result.client_id == oauth_credential.client_id
        assert result.client_secret == oauth_credential.client_secret
        assert result.scopes == oauth_credential.scopes
        assert result.expiry == oauth_credential.expiry
        assert result.email_address == oauth_credential.email_address
        asyncify.assert_not_called()

    async def test_expired_credential_returns_refreshed_credential_payload(
        self,
        oauth_credential,
    ) -> None:
        refreshed_expiry = datetime.now(UTC) + timedelta(hours=2)
        credentials = Mock()
        credentials.expired = True
        credentials.token = "refreshed-access-token"
        credentials.refresh_token = "refreshed-refresh-token"
        credentials.token_uri = oauth_credential.token_uri
        credentials.client_id = oauth_credential.client_id
        credentials.client_secret = oauth_credential.client_secret
        credentials.scopes = ["scope-a", "scope-b"]
        credentials.expiry = refreshed_expiry
        refresh = AsyncMock()

        with (
            patch(
                "src.google.service.client._convert_to_google_credential",
                return_value=credentials,
            ),
            patch("src.google.service.client.asyncer.asyncify", return_value=refresh),
        ):
            result = await fetch_refreshed_google_oauth_credential(oauth_credential)

        assert result.access_token == "refreshed-access-token"
        assert result.refresh_token == "refreshed-refresh-token"
        assert result.scopes == "scope-a,scope-b"
        assert result.expiry == refreshed_expiry
        refresh.assert_awaited_once()
