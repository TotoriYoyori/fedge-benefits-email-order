from unittest.mock import MagicMock, patch

from fastapi import status
import pytest
from src.notification.schemas import EmailProviderName, EmailSendResponse


@pytest.fixture
def mock_email_service():
    with patch("src.notification.router.send_email") as mock:
        mock.return_value = EmailSendResponse(id="test_id", provider=EmailProviderName.MAILTRAP)
        yield mock


async def test_send_notification_merchant(client, jwt_token, mock_email_service):
    token = await jwt_token("merchant")
    response = await client.post(
        "/api/v1/notification/",
        json={
            "toEmail": "test@example.com",
            "name": "John Doe",
            "treatment": "Massage"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert data["id"] == "test_id"

    mock_email_service.assert_called_once()


async def test_send_notification_admin(client, jwt_token, mock_email_service):
    token = await jwt_token("admin")
    response = await client.post(
        "/api/v1/notification/",
        json={
            "toEmail": "test@example.com"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    mock_email_service.assert_called_once()


async def test_send_notification_unauthorized(client, jwt_token):
    # 'user' role is not allowed (only merchant, admin). Wrong role collapses
    # into the same generic "not found" response as no token at all — never
    # a distinguishable 403.
    token = await jwt_token("user")
    response = await client.post(
        "/api/v1/notification/",
        json={"toEmail": "test@example.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Not found."}


async def test_send_notification_no_auth(client):
    response = await client.post(
        "/api/v1/notification/",
        json={"toEmail": "test@example.com"}
    )
    # router.post uses require_role, which uses valid_access_token.
    # valid_access_token raises UnauthenticatedUser if no access_token, and
    # the shared auth exception handler now maps that to a generic 404
    # rather than a distinguishable 401 — see auth.exceptions for why.
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Not found."}


async def test_preview_template(client):
    response = await client.get("/api/v1/notification/templates?name=John&treatment=Massage")

    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers["content-type"]
    assert "John" in response.text
