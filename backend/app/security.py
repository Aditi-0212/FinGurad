"""Small dependency-free password and signed-session helpers."""

import base64
import hashlib
import hmac
import json
import secrets
import time

from app.config import get_settings


def _secret():
    settings = get_settings()
    return (settings.auth_secret or settings.database_url).encode("utf-8")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310000)
    return base64.urlsafe_b64encode(salt + hashed).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        raw = base64.urlsafe_b64decode(password_hash.encode("ascii"))
        salt, expected = raw[:16], raw[16:]
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310000)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def issue_token(account_id: str, user_id: int, name: str, email: str) -> str:
    payload = {
        "account_id": account_id,
        "user_id": user_id,
        "name": name,
        "email": email,
        "exp": int(time.time()) + 7 * 24 * 60 * 60,
    }
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=")
    signature = hmac.new(_secret(), body, hashlib.sha256).digest()
    return body.decode() + "." + base64.urlsafe_b64encode(signature).rstrip(b"=").decode()


def read_token(token: str) -> dict:
    try:
        body, signature = token.split(".", 1)
        supplied = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        expected = hmac.new(_secret(), body.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(supplied, expected):
            raise ValueError("Invalid session signature")
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("Session expired")
        return payload
    except Exception as exc:
        raise ValueError("Invalid or expired session") from exc


def workspace_schema(account_id: str) -> str:
    return "ws_" + account_id.replace("-", "")
