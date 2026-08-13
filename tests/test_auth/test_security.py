from src.auth.schemas import Token
from src.auth.service.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hashing():
    password = "secret_password"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_jwt_token_flow():
    data = {"sub": "1", "role": "admin"}
    token_obj = create_access_token(data)
    assert isinstance(token_obj, Token)
    
    payload = decode_access_token(token_obj.access_token)
    assert payload["sub"] == "1"
    assert payload["role"] == "admin"


def test_invalid_jwt_token():
    payload = decode_access_token("invalid.access_token.here")
    assert payload is None
