"""Symmetric encryption for secrets-at-rest (Section 15), e.g. the Bambu
LAN access code stored on `Printer.access_code_encrypted`.

Derives a Fernet key from `Settings.secret_key` so we don't need a
second secret to manage; rotating `SCHOOLPRINT_SECRET_KEY` invalidates
stored access codes, which is an acceptable tradeoff for an MVP (the
teacher just re-enters the printer's access code).
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

settings = get_settings()


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Stored secret could not be decrypted (key mismatch?).") from exc
