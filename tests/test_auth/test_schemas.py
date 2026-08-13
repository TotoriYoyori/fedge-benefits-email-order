import datetime as dt

from pydantic import ValidationError
import pytest

from src.auth.schemas import AuthCreate, AuthResponse, UserPrivate


def test_auth_create_schema_valid():
    data = {
        "username": "validuser",
        "email": "valid@example.com",
        "password": "securepassword"
    }
    schema = AuthCreate(**data)
    assert schema.username == "validuser"


def test_auth_create_schema_invalid_email():
    with pytest.raises(ValidationError):
        AuthCreate(username="user", email="not-an-email", password="password123")


def test_auth_create_schema_short_password():
    with pytest.raises(ValidationError):
        AuthCreate(username="user", email="user@example.com", password="short")


def test_auth_create_schema_extra_fields():
    data = {
        "username": "extrauser",
        "email": "extra@example.com",
        "password": "password123",
        "extra_field": "should_be_ignored"
    }
    schema = AuthCreate(**data)
    
    assert schema.username == "extrauser"
    assert not hasattr(schema, "extra_field")
    # Pydantic by default ignores extra fields if not configured otherwise
    assert "extra_field" not in schema.model_dump()


def test_auth_response_schema_extra_fields():
    data = {
        "id": 1,
        "username": "respuser",
        "email": "resp@example.com",
        "role": "user",
        "authentication_time": "2024-08-24 10-00-00",
        "unexpected_data": "malicious_payload"
    }
    schema = AuthResponse(**data)

    assert not hasattr(schema, "unexpected_data")
    assert schema.username == "respuser"
    assert "unexpected_data" not in schema.model_dump()


def test_user_private_schema_valid():
    now = dt.datetime.now()
    data = {
        "id": 1,
        "username": "privateuser",
        "email": "private@example.com",
        "role": "user",
        "authentication_time": "2024-08-24 10-00-00",
        "registration_time": now,
        "password_hash": "hashed_pw_here_is_long_enough",
        "message": "Custom welcome"
    }
    schema = UserPrivate(**data)
    
    assert schema.username == "privateuser"
    assert schema.password_hash == "hashed_pw_here_is_long_enough"
    assert schema.registration_time == now

    resp_schema = AuthResponse(**data)
    assert "password_hash" not in resp_schema.model_dump()
