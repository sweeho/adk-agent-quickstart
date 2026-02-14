"""FastAPI dependencies for authentication and authorization."""

from fastapi import Header, HTTPException, Depends

from adk_web_agent.auth.jwt_helper import verify_token


async def get_current_user(authorization: str = Header(default=None)) -> dict:
    """Extract and validate user from JWT token in Authorization header.

    Returns dict with 'user_id' and 'is_admin' keys.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = verify_token(token)
        return {
            "user_id": payload["user_id"],
            "is_admin": payload["is_admin"],
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require the current user to have admin privileges."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
