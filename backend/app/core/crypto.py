"""Symmetric encryption for stored credentials (Fernet = AES-128-CBC + HMAC-SHA256).

Production: set ENCRYPTION_KEYS (store in your secrets manager, NOT in the database).
Rotation: prepend a new key, keep the old one until all rows are re-encrypted.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.core.config import settings


def _cipher() -> MultiFernet:
    keys = [k.strip() for k in (settings.encryption_keys or "").split(",") if k.strip()]
    if not keys:  # dev fallback derived from SECRET_KEY. Set ENCRYPTION_KEYS in production.
        keys = [base64.urlsafe_b64encode(hashlib.sha256(f"shapater-dev:{settings.secret_key}".encode()).digest()).decode()]
    return MultiFernet([Fernet(k) for k in keys])


def encrypt(plain: str) -> str:
    return _cipher().encrypt(plain.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _cipher().decrypt(token.encode()).decode()
    except InvalidToken as e:
        raise ValueError("Cannot decrypt value (wrong or rotated ENCRYPTION_KEYS)") from e
