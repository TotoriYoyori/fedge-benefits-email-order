import pytest
from fastapi import status
from httpx import Response

from tests.abstracts import TestRoute


# =============== /oauth2 ROUTE ===============
class TestOAuth2Route(TestRoute):
    route_url = "/api/v1/google/oauth2"

    async def request_route(self, token: str | None = None) -> Response:
        headers = {"Authorization": f"Bearer {token}"} if token else None

        return await self.client.post(self.route_url, headers=headers)

    @pytest.mark.parametrize("role", ["merchant", "admin"])
    async def test_accepted_roles(self, mock_initiate_oauth2, role: str):
        token = await self.jwt_token(role)
        response = await self.request_route(token=token)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "authUrl": mock_initiate_oauth2.return_value.auth_url,
            "message": "You are being redirected to Google for authorization.",
        }
        mock_initiate_oauth2.assert_awaited_once()
        _, valid_user_id = mock_initiate_oauth2.await_args.args

        assert valid_user_id == 1

    @pytest.mark.parametrize("role", ["user"])
    async def test_rejected_roles(self, mock_initiate_oauth2, role):
        token = await self.jwt_token(role)
        response = await self.request_route(token=token)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_initiate_oauth2.assert_not_awaited()

    async def test_requires_authentication(self, mock_initiate_oauth2):
        response = await self.request_route()

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        mock_initiate_oauth2.assert_not_awaited()


# =============== /callback ROUTE ===============
class TestCallbackRoute(TestRoute):
    route_url = "/api/v1/google/callback"

    async def request_route(self, code: str | None = None, state: str | None = None) -> Response:
        params = {
            key: value
            for key, value in {"code": code, "state": state}.items()
            if value is not None
        }
        return await self.client.get(self.route_url, params=params)

    async def test_missing_exchange_code(self, mock_exchange_code_for_credentials):
        response = await self.request_route(state="OVMhZYD07kJtW1uA7nW1bTYk3AZ0ZJ")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": "Invalid Google OAuth callback. Please restart the Google OAuth flow."
        }
        mock_exchange_code_for_credentials.assert_not_awaited()

    async def test_missing_oauth_state(self, mock_exchange_code_for_credentials):
        response = await self.request_route(code="google-exchange-code")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": "Invalid Google OAuth callback. Please restart the Google OAuth flow."
        }
        mock_exchange_code_for_credentials.assert_not_awaited()

    async def test_returns_credentials_response(
        self,
        mock_exchange_code_for_credentials,
        override_valid_google_oauth2_state,
    ):
        response = await self.request_route(
            code="google-exchange-code",
            state=override_valid_google_oauth2_state.state,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "userId": 1,
            "scopes": "openid,email,https://www.googleapis.com/auth/gmail.readonly",
            "expiry": mock_exchange_code_for_credentials.return_value.expiry.isoformat().replace("+00:00", "Z"),
            "emailAddress": "merchant@example.com",
            "message": "Successfully connected to Google using OAuth 2.0!",
        }

        mock_exchange_code_for_credentials.assert_awaited_once()
        _, exchange_code, returned_oauth_state = mock_exchange_code_for_credentials.await_args.args

        assert exchange_code == "google-exchange-code"
        assert returned_oauth_state is override_valid_google_oauth2_state


# =============== /me ROUTE ===============
class TestMeRoute(TestRoute):
    route_url = "/api/v1/google/me"

    async def request_route(self, token: str | None = None) -> Response:
        headers = {"Authorization": f"Bearer {token}"} if token else None

        return await self.client.get(self.route_url, headers=headers)

    async def test_returns_credential_response(self, override_valid_google_oauth_credential):
        token = await self.jwt_token("merchant")
        response = await self.request_route(token=token)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "userId": 1,
            "scopes": "openid,email,https://www.googleapis.com/auth/gmail.readonly",
            "expiry": override_valid_google_oauth_credential.expiry.isoformat().replace("+00:00", "Z"),
            "emailAddress": "merchant@example.com",
            "message": "Successfully connected to Google using OAuth 2.0!",
        }

    async def test_missing_oauth_credential(self):
        token = await self.jwt_token("merchant")
        response = await self.request_route(token=token)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": (
                "Google OAuth user_google_credential is invalid. Please redo the Google "
                "OAuth flow to obtain a new user_google_credential."
            )
        }


# =============== /gmail ROUTE ===============
class TestGmailRoute(TestRoute):
    route_url = "/api/v1/google/gmail"

    async def request_route(self, token: str | None = None) -> Response:
        headers = {"Authorization": f"Bearer {token}"} if token else None

        return await self.client.post(self.route_url, headers=headers)

    async def test_returns_credential_response(
        self,
        mock_connect_gmail_service,
        override_valid_google_oauth_credential,
    ):
        token = await self.jwt_token("merchant")
        response = await self.request_route(token=token)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "userId": 1,
            "scopes": "openid,email,https://www.googleapis.com/auth/gmail.readonly",
            "expiry": mock_connect_gmail_service.return_value.expiry.isoformat().replace("+00:00", "Z"),
            "emailAddress": "merchant@example.com",
            "message": "Successfully connected to Google using OAuth 2.0!",
        }
        mock_connect_gmail_service.assert_awaited_once()
        _, returned_credential = mock_connect_gmail_service.await_args.args

        assert returned_credential is override_valid_google_oauth_credential

    async def test_missing_oauth_credential(self):
        token = await self.jwt_token("merchant")
        response = await self.request_route(token=token)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": (
                "Google OAuth user_google_credential is invalid. Please redo the Google "
                "OAuth flow to obtain a new user_google_credential."
            )
        }
