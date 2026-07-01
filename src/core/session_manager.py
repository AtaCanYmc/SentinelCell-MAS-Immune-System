import base64
import hmac
import hashlib
import json
import os
import time

SECRET_KEY = os.getenv(
    "API_KEY_SECRET", "sentinel-default-secret-key-32-chars-long"
).encode()


def create_session_token(username: str, expires_in: int = 3600) -> str:
    """Generates a secure HMAC-SHA256 signed session token."""
    payload = {
        "username": username,
        "expires": time.time() + expires_in,
    }
    payload_json = json.dumps(payload).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode("utf-8")

    # Generate HMAC signature
    signature = hmac.new(
        SECRET_KEY, payload_b64.encode("utf-8"), hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode("utf-8")

    return f"{payload_b64}.{signature_b64}"


def verify_session_token(token: str) -> str | None:
    """Verifies the HMAC signature and expiration of the session token."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None

        payload_b64, signature_b64 = parts

        # Verify signature
        expected_sig = hmac.new(
            SECRET_KEY, payload_b64.encode("utf-8"), hashlib.sha256
        ).digest()
        actual_sig = base64.urlsafe_b64decode(signature_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        # Decode payload and check expiration
        payload_json = base64.urlsafe_b64decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_json)

        if time.time() > payload.get("expires", 0):
            return None  # Token expired

        return payload.get("username")
    except Exception:
        return None
