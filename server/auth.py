"""Authentication primitives used by the authoritative server."""

import base64
import hashlib
import hmac
import struct
import time
from typing import Any


def password_hash(username: str, password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), (username + salt).encode(), 120_000
    ).hex()


def safe_username(value: Any) -> str:
    return "".join(
        character for character in str(value).strip().lower()
        if character.isalnum() or character in "_-."
    )[:32]


def mfa_code(secret: str, timestamp: int | None = None) -> str:
    counter = int(time.time() // 30) if timestamp is None else int(timestamp // 30)
    digest = hmac.new(
        base64.b32decode(secret + "=" * ((8 - len(secret) % 8) % 8)),
        struct.pack(">Q", counter),
        hashlib.sha1,
    ).digest()
    offset = digest[-1] & 15
    number = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7fffffff) % 1_000_000
    return f"{number:06d}"
