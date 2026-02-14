"""Admin routes for user management. All endpoints require admin privileges."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from adk_web_agent.auth.middleware import require_admin
from adk_web_agent.auth.password import hash_password
from adk_web_agent.database.db import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    user_id: str  # email
    password: str
    is_admin: bool = False
    is_active: bool = True


class UpdateUserRequest(BaseModel):
    is_admin: bool | None = None
    is_active: bool | None = None


class ResetPasswordRequest(BaseModel):
    new_password: str


def _format_user(row) -> dict:
    """Convert a database row to a user dict (no password_hash)."""
    return {
        "user_id": row["user_id"],
        "is_active": bool(row["is_active"]),
        "is_admin": bool(row["is_admin"]),
        "created_at": row["created_at"],
        "last_login": row["last_login"],
    }


@router.get("/users")
async def list_users(admin: dict = Depends(require_admin)):
    """List all users."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT user_id, is_active, is_admin, created_at, last_login FROM users ORDER BY created_at"
        )
        rows = await cursor.fetchall()
        return {"users": [_format_user(r) for r in rows]}
    finally:
        await db.close()


@router.post("/users")
async def create_user(req: CreateUserRequest, admin: dict = Depends(require_admin)):
    """Create a new user."""
    db = await get_db()
    try:
        # Check if user already exists
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?", (req.user_id,)
        )
        if await cursor.fetchone():
            raise HTTPException(status_code=409, detail="User already exists")

        hashed = hash_password(req.password)
        await db.execute(
            """INSERT INTO users (user_id, password_hash, is_admin, is_active)
               VALUES (?, ?, ?, ?)""",
            (req.user_id, hashed, req.is_admin, req.is_active),
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT user_id, is_active, is_admin, created_at, last_login FROM users WHERE user_id = ?",
            (req.user_id,),
        )
        row = await cursor.fetchone()
        return {"user": _format_user(row)}
    finally:
        await db.close()


@router.put("/users/{user_id}")
async def update_user(
    user_id: str, req: UpdateUserRequest, admin: dict = Depends(require_admin)
):
    """Update user flags (admin, active)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT user_id, is_admin FROM users WHERE user_id = ?", (user_id,)
        )
        existing = await cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")

        # Cannot remove own admin flag
        if user_id == admin["user_id"] and req.is_admin is False:
            raise HTTPException(
                status_code=400, detail="Cannot remove your own admin privileges"
            )

        updates = []
        params: list = []
        if req.is_admin is not None:
            updates.append("is_admin = ?")
            params.append(req.is_admin)
        if req.is_active is not None:
            updates.append("is_active = ?")
            params.append(req.is_active)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(user_id)
        await db.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?", params
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT user_id, is_active, is_admin, created_at, last_login FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        return {"user": _format_user(row)}
    finally:
        await db.close()


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: str, req: ResetPasswordRequest, admin: dict = Depends(require_admin)
):
    """Reset a user's password."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        hashed = hash_password(req.new_password)
        await db.execute(
            "UPDATE users SET password_hash = ? WHERE user_id = ?",
            (hashed, user_id),
        )
        await db.commit()
        return {"success": True}
    finally:
        await db.close()


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
    """Delete a user and cascade-delete their sessions."""
    db = await get_db()
    try:
        # Cannot delete self
        if user_id == admin["user_id"]:
            raise HTTPException(
                status_code=400, detail="Cannot delete your own account"
            )

        cursor = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        # Ensure at least one admin remains
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE is_admin = TRUE AND user_id != ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        admin_count = row[0] if row else 0

        cursor2 = await db.execute(
            "SELECT is_admin FROM users WHERE user_id = ?", (user_id,)
        )
        target = await cursor2.fetchone()
        if target and target["is_admin"] and admin_count < 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last admin user",
            )

        await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        await db.commit()
        return {"success": True}
    finally:
        await db.close()
