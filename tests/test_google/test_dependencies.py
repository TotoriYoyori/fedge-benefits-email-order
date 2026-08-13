from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.google.dependencies import (
    valid_google_oauth2_exchange_code,
    valid_google_oauth2_state,
    valid_google_oauth_credential,
)
from src.google.exceptions import (
    InvalidGoogleOAuthCallbackState,
    InvalidGoogleOAuthCredential,
)


# =============== valid_google_oauth2_exchange_code ===============
class TestValidGoogleOAuth2ExchangeCode:
    def test_returns_exchange_code(self):
        exchange_code = "google-exchange-code"

        result = valid_google_oauth2_exchange_code(exchange_code)

        assert result == exchange_code

    def test_missing_exchange_code(self):
        with pytest.raises(InvalidGoogleOAuthCallbackState):
            valid_google_oauth2_exchange_code(None)


# =============== valid_google_oauth2_state ===============
class TestValidGoogleOAuth2State:
    async def test_happy_path_returns_oauth_state(self, fake_db, oauth_state):
        with (
            patch(
                "src.google.dependencies.get_state",
                new=AsyncMock(return_value=oauth_state),
            ) as mock_get_state,
            patch(
                "src.google.dependencies.state_is_stale",
                new=Mock(return_value=False),
            ) as mock_state_is_stale,
        ):
            result = await valid_google_oauth2_state(fake_db, oauth_state.state)

        assert result is oauth_state
        mock_get_state.assert_awaited_once_with(fake_db, oauth_state.state)
        mock_state_is_stale.assert_called_once_with(oauth_state)

    async def test_missing_callback_state(self, fake_db):
        with patch("src.google.dependencies.get_state", new=AsyncMock()) as mock_get_state:
            with pytest.raises(InvalidGoogleOAuthCallbackState):
                await valid_google_oauth2_state(fake_db, None)

        mock_get_state.assert_not_awaited()

    async def test_junk_param_raises_invalid_callback_state(self, fake_db):
        junk_state = "not-a-real-state"

        with (
            patch(
                "src.google.dependencies.get_state",
                new=AsyncMock(return_value=None),
            ) as mock_get_state,
            patch(
                "src.google.dependencies.state_is_stale",
                new=Mock(),
            ) as mock_state_is_stale,
        ):
            with pytest.raises(InvalidGoogleOAuthCallbackState):
                await valid_google_oauth2_state(fake_db, junk_state)

        mock_get_state.assert_awaited_once_with(fake_db, junk_state)
        mock_state_is_stale.assert_not_called()


# =============== valid_google_oauth_credential ===============
class TestValidGoogleOAuthCredential:
    async def test_happy_path_returns_oauth_credential(
        self,
        fake_db,
        valid_user,
        oauth_credential,
    ):
        with (
            patch(
                "src.google.dependencies.get_oauth_credential",
                new=AsyncMock(return_value=oauth_credential),
            ) as mock_get_oauth_credential,
            patch(
                "src.google.dependencies.credential_is_stale",
                new=Mock(return_value=False),
            ) as mock_credential_is_stale,
        ):
            result = await valid_google_oauth_credential(valid_user, fake_db)

        assert result is oauth_credential
        mock_get_oauth_credential.assert_awaited_once_with(fake_db, valid_user.id)
        mock_credential_is_stale.assert_called_once_with(oauth_credential)

    async def test_missing_param_raises_invalid_google_oauth_credential(
        self,
        fake_db,
        valid_user,
    ):
        with patch(
            "src.google.dependencies.get_oauth_credential",
            new=AsyncMock(return_value=None),
        ) as mock_get_oauth_credential:
            with pytest.raises(InvalidGoogleOAuthCredential):
                await valid_google_oauth_credential(valid_user, fake_db)

        mock_get_oauth_credential.assert_awaited_once_with(fake_db, valid_user.id)

    async def test_junk_param_raises_invalid_google_oauth_credential(
        self,
        fake_db,
        valid_user,
        oauth_credential,
    ):
        with (
            patch(
                "src.google.dependencies.get_oauth_credential",
                new=AsyncMock(return_value=oauth_credential),
            ) as mock_get_oauth_credential,
            patch(
                "src.google.dependencies.credential_is_stale",
                new=Mock(return_value=True),
            ) as mock_credential_is_stale,
        ):
            with pytest.raises(InvalidGoogleOAuthCredential):
                await valid_google_oauth_credential(valid_user, fake_db)

        mock_get_oauth_credential.assert_awaited_once_with(fake_db, valid_user.id)
        mock_credential_is_stale.assert_called_once_with(oauth_credential)
