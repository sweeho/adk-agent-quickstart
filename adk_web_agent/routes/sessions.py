"""Session management routes with user isolation."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from adk_web_agent.auth.middleware import get_current_user
from adk_web_agent.database.db import get_db

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    session_name: str | None = None


class UpdateSessionRequest(BaseModel):
    session_name: str | None = None


def _format_session(row) -> dict:
    """Convert a database row to a session dict."""
    return {
        "session_id": row["session_id"],
        "user_id": row["user_id"],
        "session_name": row["session_name"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "message_count": row["message_count"],
        "last_message_preview": row["last_message_preview"],
        "agent_count": row["agent_count"],
    }


@router.get("")
async def list_sessions(user: dict = Depends(get_current_user)):
    """List all sessions for the authenticated user."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT session_id, user_id, session_name, created_at, updated_at,
                      message_count, last_message_preview, agent_count
               FROM sessions
               WHERE user_id = ?
               ORDER BY updated_at DESC""",
            (user["user_id"],),
        )
        rows = await cursor.fetchall()
        return {"sessions": [_format_session(r) for r in rows]}
    finally:
        await db.close()


@router.post("")
async def create_session(
    req: CreateSessionRequest = CreateSessionRequest(),
    user: dict = Depends(get_current_user),
):
    """Create a new session for the authenticated user."""
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    name = req.session_name or f"New Chat - {datetime.now(timezone.utc).strftime('%b %d')}"

    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO sessions (session_id, user_id, session_name, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, user["user_id"], name, now, now),
        )
        await db.commit()

        return {
            "session": {
                "session_id": session_id,
                "user_id": user["user_id"],
                "session_name": name,
                "created_at": now,
                "updated_at": now,
                "message_count": 0,
                "last_message_preview": None,
                "agent_count": 0,
            }
        }
    finally:
        await db.close()


@router.get("/{session_id}")
async def get_session(session_id: str, user: dict = Depends(get_current_user)):
    """Get a session by ID, verifying ownership."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT session_id, user_id, session_name, created_at, updated_at,
                      message_count, last_message_preview, agent_count
               FROM sessions
               WHERE session_id = ? AND user_id = ?""",
            (session_id, user["user_id"]),
        )
        row = await cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"session": _format_session(row)}
    finally:
        await db.close()


@router.put("/{session_id}")
async def update_session(
    session_id: str,
    req: UpdateSessionRequest,
    user: dict = Depends(get_current_user),
):
    """Update a session (rename), verifying ownership."""
    db = await get_db()
    try:
        # Verify ownership
        cursor = await db.execute(
            "SELECT session_id FROM sessions WHERE session_id = ? AND user_id = ?",
            (session_id, user["user_id"]),
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Session not found")

        now = datetime.now(timezone.utc).isoformat()
        updates = ["updated_at = ?"]
        params: list = [now]

        if req.session_name is not None:
            updates.append("session_name = ?")
            params.append(req.session_name)

        params.extend([session_id, user["user_id"]])

        await db.execute(
            f"UPDATE sessions SET {', '.join(updates)} WHERE session_id = ? AND user_id = ?",
            params,
        )
        await db.commit()

        # Return updated session
        cursor = await db.execute(
            """SELECT session_id, user_id, session_name, created_at, updated_at,
                      message_count, last_message_preview, agent_count
               FROM sessions
               WHERE session_id = ? AND user_id = ?""",
            (session_id, user["user_id"]),
        )
        row = await cursor.fetchone()
        return {"session": _format_session(row)}
    finally:
        await db.close()


@router.delete("/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    """Delete a session, verifying ownership. Cascade deletes messages/executions."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT session_id FROM sessions WHERE session_id = ? AND user_id = ?",
            (session_id, user["user_id"]),
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Session not found")

        await db.execute(
            "DELETE FROM sessions WHERE session_id = ? AND user_id = ?",
            (session_id, user["user_id"]),
        )
        await db.commit()

        return {"success": True}
    finally:
        await db.close()
