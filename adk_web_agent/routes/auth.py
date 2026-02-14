"""Authentication routes: login, validate, logout."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from adk_web_agent.auth.jwt_helper import create_access_token
from adk_web_agent.auth.middleware import get_current_user
from adk_web_agent.auth.password import verify_password
from adk_web_agent.database.db import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    user_id: str
    password: str


@router.post("/login")
async def login(req: LoginRequest):
    """Authenticate user and return JWT token."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT user_id, password_hash, is_active, is_admin, last_login FROM users WHERE user_id = ?",
            (req.user_id,),
        )
        row = await cursor.fetchone()

        if not row:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not row["is_active"]:
            raise HTTPException(status_code=401, detail="Account is disabled")

        if not verify_password(req.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Update last_login
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE users SET last_login = ? WHERE user_id = ?",
            (now, req.user_id),
        )
        await db.commit()

        token = create_access_token(row["user_id"], bool(row["is_admin"]))

        return {
            "token": token,
            "user": {
                "user_id": row["user_id"],
                "is_admin": bool(row["is_admin"]),
                "last_login": now,
            },
        }
    finally:
        await db.close()


@router.get("/validate")
async def validate(user: dict = Depends(get_current_user)):
    """Validate current JWT token."""
    return {
        "valid": True,
        "user_id": user["user_id"],
        "is_admin": user["is_admin"],
    }


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """Logout (stateless — placeholder for future token blocklist)."""
    return {"success": True}
