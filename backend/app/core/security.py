"""
Security utilities: password hashing, JWT, AES encryption.
Uses bcrypt directly (no passlib) to avoid version incompatibilities.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from fastapi import HTTPException, status
import bcrypt
import os
import base64

SECRET_KEY  = os.getenv("SECRET_KEY", "vcm-default-secret-change-in-production")
ALGORITHM   = "HS256"
TOKEN_EXP   = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

_raw_enc = os.getenv("ENCRYPTION_KEY", "")
if not _raw_enc:
    _raw_enc = base64.urlsafe_b64encode(b"vcm-enc-key-32bytes-padding-here").decode()
try:
    fernet = Fernet(_raw_enc.encode() if len(_raw_enc) == 44
                    else base64.urlsafe_b64encode(_raw_enc.encode()[:32]))
except Exception:
    fernet = Fernet(Fernet.generate_key())


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a bcrypt hash.
    Returns False (never raises) so callers always get a clean bool.
    """
    try:
        plain_bytes  = plain.encode("utf-8")
        hashed_bytes = hashed.encode("utf-8") if isinstance(hashed, str) else hashed
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password with bcrypt (cost 12)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = {**data, "exp": datetime.utcnow() + (expires_delta or timedelta(minutes=TOKEN_EXP))}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def encrypt_value(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    return fernet.decrypt(encrypted.encode()).decode()
