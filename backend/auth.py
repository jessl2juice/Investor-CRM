"""
BetterMind CRM - Authentication
Token creation, verification, and FastAPI dependencies for auth.
"""
import hashlib
import hmac
import json
import base64
import logging
import os
import secrets
import time

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

_configured_secret = os.environ.get("TOKEN_SECRET", "")
if not _configured_secret:
    logger.warning("TOKEN_SECRET env var not set -- generating ephemeral secret. Tokens will not survive restarts.")
    _configured_secret = secrets.token_hex(32)

TOKEN_SECRET = _configured_secret
TOKEN_TTL = 86400 * 7  # 7 days


def make_token(email: str, role: str = "user") -> str:
    """Create a signed HMAC token with embedded claims."""
    ts = str(int(time.time()))
    payload = base64.b64encode(json.dumps({"email": email, "role": role}).encode()).decode()
    msg = f"{ts}.{payload}"
    sig = hmac.new(TOKEN_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return f"{ts}.{payload}.{sig}"


def verify_token(token: str) -> dict | None:
    """Verify an HMAC token and return claims, or None if invalid/expired."""
    try:
        ts, payload, sig = token.split(".", 2)
        expected = hmac.new(TOKEN_SECRET.encode(), f"{ts}.{payload}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if time.time() - int(ts) > TOKEN_TTL:
            return None
        return json.loads(base64.b64decode(payload))
    except Exception:
        return None


def require_auth(request: Request) -> dict:
    """FastAPI dependency: require a valid Bearer token."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        claims = verify_token(auth[7:])
        if claims:
            return claims
    raise HTTPException(401, "Unauthorized")


def require_admin(request: Request) -> dict:
    """FastAPI dependency: require a valid Bearer token with admin role."""
    claims = require_auth(request)
    if claims.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    return claims
