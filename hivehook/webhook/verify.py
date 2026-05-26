from __future__ import annotations

import hashlib
import hmac
import os
import time

HEADER_SIGNATURE = "X-Hivehook-Signature"
HEADER_TIMESTAMP = "X-Hivehook-Timestamp"
HEADER_MESSAGE_ID = "X-Hivehook-Message-ID"

DEFAULT_TOLERANCE = 300


def generate_secret() -> str:
    return "whsec_" + os.urandom(32).hex()


def sign(payload: str | bytes, secret: str, timestamp: int | None = None) -> tuple[str, int]:
    if timestamp is None:
        timestamp = int(time.time())
    if isinstance(payload, str):
        payload = payload.encode()
    signing_input = f"{timestamp}.".encode() + payload
    raw_secret = _decode_secret(secret)
    mac = hmac.new(raw_secret, signing_input, hashlib.sha256)
    sig = f"v1={mac.hexdigest()}"
    return sig, timestamp


def _extract_v1(signature: str) -> str | None:
    """Extract the v1=... element from a possibly multi-scheme signature header.

    Supports headers like:
        v1=abc...
        v1=abc...,v0=foo
        t=123,v1=abc...
    Returns None if no v1= element is present.
    """
    if not signature:
        return None
    for part in signature.split(","):
        part = part.strip()
        if part.startswith("v1="):
            return part
    return None


def verify(
    payload: str | bytes,
    secret: str,
    signature: str,
    timestamp: int | str,
    tolerance: int = DEFAULT_TOLERANCE,
) -> bool:
    try:
        ts = int(timestamp) if isinstance(timestamp, str) else timestamp
    except (TypeError, ValueError):
        return False
    if tolerance > 0:
        now = int(time.time())
        if abs(now - ts) > tolerance:
            return False
    provided = _extract_v1(signature)
    if provided is None:
        return False
    expected_sig, _ = sign(payload, secret, ts)
    return hmac.compare_digest(expected_sig, provided)


def verify_with_rotation(
    payload: str | bytes,
    primary_secret: str,
    secondary_secret: str | None,
    signature: str,
    timestamp: int | str,
    tolerance: int = DEFAULT_TOLERANCE,
) -> bool:
    if verify(payload, primary_secret, signature, timestamp, tolerance):
        return True
    if secondary_secret:
        return verify(payload, secondary_secret, signature, timestamp, tolerance)
    return False


def _decode_secret(secret: str) -> bytes:
    return secret.encode()
