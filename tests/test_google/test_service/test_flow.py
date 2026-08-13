from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from src.google.schemas import GoogleOAuth2CredentialCreate
from src.google.service.flow import sync_access_token


class TestSyncAccessToken:
    async def test_unchanged_credential_skips_persistence(self, fake_db, oauth_credential) -> None:
        credential_payload = GoogleOAuth2CredentialCreate(
            user_id=oauth_credential.user_id,
            access_token=oauth_credential.access_token,
            refresh_token=oauth_credential.refresh_token,
            token_uri=oauth_credential.token_uri,
            client_id=oauth_credential.client_id,
            client_secret=oauth_credential.client_secret,
            scopes=oauth_credential.scopes,
            expiry=oauth_credential.expiry,
            email_address=oauth_credential.email_address,
        )

        with (
            patch(
                "src.google.service.flow.fetch_refreshed_google_oauth_credential",
                new=AsyncMock(return_value=credential_payload),
            ) as fetch_refreshed,
            patch("src.google.service.flow.refresh_oauth_access_token") as refresh_token,
        ):
            result = await sync_access_token(fake_db, oauth_credential)

        assert result is oauth_credential
        fetch_refreshed.assert_awaited_once_with(oauth_credential)
        refresh_token.assert_not_called()

    async def test_changed_credential_is_persisted(self, fake_db, oauth_credential) -> None:
        credential_payload = GoogleOAuth2CredentialCreate(
            user_id=oauth_credential.user_id,
            access_token="refreshed-access-token",
            refresh_token=oauth_credential.refresh_token,
            token_uri=oauth_credential.token_uri,
            client_id=oauth_credential.client_id,
            client_secret=oauth_credential.client_secret,
            scopes=oauth_credential.scopes,
            expiry=datetime.now(UTC) + timedelta(hours=2),
            email_address=oauth_credential.email_address,
        )
        persisted_credential = object()

        with (
            patch(
                "src.google.service.flow.fetch_refreshed_google_oauth_credential",
                new=AsyncMock(return_value=credential_payload),
            ),
            patch(
                "src.google.service.flow.refresh_oauth_access_token",
                new=AsyncMock(return_value=persisted_credential),
            ) as refresh_token,
        ):
            result = await sync_access_token(fake_db, oauth_credential)

        assert result is persisted_credential
        refresh_token.assert_awaited_once_with(
            fake_db,
            oauth_credential,
            credential_payload,
        )
