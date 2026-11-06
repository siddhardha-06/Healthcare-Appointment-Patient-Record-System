"""HAP-SR-006: AES-256-GCM helpers."""
import base64

import pytest

from app.core import crypto
from app.core.config import reload_settings


def test_round_trip_and_random_nonce():
    a, b = crypto.encrypt("Viral fever"), crypto.encrypt("Viral fever")
    assert a != b and a.startswith("v1:") and "Viral" not in a
    assert crypto.decrypt(a) == crypto.decrypt(b) == "Viral fever"
    assert crypto.encrypt(None) is None and crypto.decrypt(None) is None


def test_tampering_is_detected():
    token = crypto.encrypt("Dengue fever")
    raw = bytearray(base64.b64decode(token[3:]))
    raw[-1] ^= 1
    with pytest.raises(Exception):
        crypto.decrypt("v1:" + base64.b64encode(bytes(raw)).decode())
    with pytest.raises(ValueError):
        crypto.decrypt("plain text")


def test_configured_key_is_used(monkeypatch):
    key = crypto.new_key()
    monkeypatch.setenv("HAP_DATA_KEY", key)
    reload_settings()
    token = crypto.encrypt("x")
    assert crypto.decrypt(token) == "x"
    monkeypatch.setenv("HAP_DATA_KEY", base64.b64encode(b"short").decode())
    reload_settings()
    with pytest.raises(ValueError):
        crypto.encrypt("x")
    monkeypatch.delenv("HAP_DATA_KEY")
    reload_settings()
