"""JWT token creation and verification."""

import os
from datetime import datetime, timedelta, timezone

import jwt

SECRET_KEY = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24


def create_access_token(user_id: str, is_admin: bool) -> str:
    """Generate a JWT access token."""
    payload = {
        "user_id": user_id,
        "is_admin": is_admin,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token. Raises on invalid/expired tokens."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
