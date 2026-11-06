"""AES-256-GCM encryption for sensitive medical fields at rest (HAP-SR-006).
The key comes from HAP_DATA_KEY (base64 of 32 bytes) and is never stored in the database."""
import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

PREFIX = "v1:"


def _key() -> bytes:
    if settings.data_key:
        key = base64.b64decode(settings.data_key)
        if len(key) != 32:
            raise ValueError("HAP_DATA_KEY must be base64 of exactly 32 bytes")
        return key
    return hashlib.sha256(("hap-dev-data-key:" + settings.jwt_secret).encode()).digest()  # development only


def encrypt(plaintext: str | None) -> str | None:
    if plaintext is None:
        return None
    nonce = os.urandom(12)
    ct = AESGCM(_key()).encrypt(nonce, plaintext.encode("utf-8"), None)
    return PREFIX + base64.b64encode(nonce + ct).decode()


def decrypt(token: str | None) -> str | None:
    if token is None:
        return None
    if not token.startswith(PREFIX):
        raise ValueError("value is not encrypted with this scheme")
    raw = base64.b64decode(token[len(PREFIX):])
    return AESGCM(_key()).decrypt(raw[:12], raw[12:], None).decode("utf-8")


def new_key() -> str:
    """Helper for operators: python -c 'from app.core.crypto import new_key; print(new_key())'"""
    return base64.b64encode(os.urandom(32)).decode()
