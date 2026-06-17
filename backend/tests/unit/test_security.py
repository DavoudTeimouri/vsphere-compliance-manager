"""Unit tests for security module."""
import pytest
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, decode_token,
    encrypt_value, decrypt_value,
)
from datetime import timedelta
from fastapi import HTTPException


class TestPasswordHashing:

    def test_hash_is_not_plaintext(self):
        hashed = get_password_hash("mypassword")
        assert hashed != "mypassword"

    def test_correct_password_verifies(self):
        hashed = get_password_hash("correct-horse")
        assert verify_password("correct-horse", hashed) is True

    def test_wrong_password_fails(self):
        hashed = get_password_hash("correct-horse")
        assert verify_password("wrong-horse", hashed) is False

    def test_empty_password_hashes(self):
        hashed = get_password_hash("")
        assert isinstance(hashed, str)
        assert len(hashed) > 0


class TestJWT:

    def test_token_creation_and_decode(self):
        token = create_access_token({"sub": "42", "role": "admin"})
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["role"] == "admin"

    def test_expired_token_raises(self):
        token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(HTTPException) as exc:
            decode_token(token)
        assert exc.value.status_code == 401

    def test_tampered_token_raises(self):
        token = create_access_token({"sub": "1"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(HTTPException):
            decode_token(tampered)

    def test_token_contains_expiry(self):
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)
        assert "exp" in payload


class TestEncryption:

    def test_encrypt_decrypt_roundtrip(self):
        original = "super-secret-vcenter-password"
        encrypted = encrypt_value(original)
        assert encrypted != original
        assert decrypt_value(encrypted) == original

    def test_encrypted_value_differs_each_time(self):
        """Fernet includes a timestamp so same input → different ciphertext."""
        val = "same-password"
        enc1 = encrypt_value(val)
        enc2 = encrypt_value(val)
        assert enc1 != enc2
        assert decrypt_value(enc1) == decrypt_value(enc2) == val

    def test_encrypt_empty_string(self):
        encrypted = encrypt_value("")
        assert decrypt_value(encrypted) == ""

    def test_encrypt_unicode(self):
        original = "رمزعبور-۱۲۳"
        assert decrypt_value(encrypt_value(original)) == original
