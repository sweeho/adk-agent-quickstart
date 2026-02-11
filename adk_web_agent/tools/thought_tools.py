"""Thought stream emission tools for real-time agent reasoning visibility."""

import uuid
from datetime import datetime
from google.adk.tools import ToolContext


def _get_thought_stream(tool_context: ToolContext) -> list:
    """Get the current thought stream from state, initializing if needed."""
    return tool_context.state.get("thought_stream", [])


def _set_thought_stream(tool_context: ToolContext, stream: list) -> None:
    """Persist the thought stream back to state."""
    # Cap at 100 entries to prevent unbounded growth
    if len(stream) > 100:
        stream = stream[-100:]
    tool_context.state["thought_stream"] = stream


def emit_thought(
    tool_context: ToolContext,
    agent_name: str,
    message: str,
    status: str = "running",
) -> dict:
    """Emit a thought step to the frontend thought stream.

    Call this tool to report what you are currently doing or have finished doing.
    Use status="running" when starting a task, and status="completed" when done.

    Args:
        tool_context: The tool context for accessing shared state.
        agent_name: Name of the agent emitting the thought (e.g. "root_agent").
        message: A brief description of the current activity.
        status: One of "running", "completed", or "error".

    Returns:
        A dict confirming the thought was emitted.
    """
    stream = _get_thought_stream(tool_context)

    if status in ("completed", "error"):
        # Update the most recent running thought for this agent
        updated = False
        for thought in reversed(stream):
            if thought["agent_name"] == agent_name and thought["status"] == "running":
                thought["status"] = status
                thought["message"] = message
                break
        # If no running thought found, add as a new entry anyway
        if not updated:
            stream.append({
                "id": str(uuid.uuid4())[:8],
                "agent_name": agent_name,
                "message": message,
                "status": status,
                "timestamp": datetime.now().isoformat(),
            })
    else:
        stream.append({
            "id": str(uuid.uuid4())[:8],
            "agent_name": agent_name,
            "message": message,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        })

    _set_thought_stream(tool_context, stream)
    return {"status": "ok", "thought_count": len(stream)}


def _emit_tool_thought(
    tool_context: ToolContext,
    agent_name: str,
    message: str,
    status: str = "running",
) -> str:
    """Internal helper for tool functions to emit thoughts.

    Returns the thought ID so callers can update it later.
    """
    stream = _get_thought_stream(tool_context)
    thought_id = str(uuid.uuid4())[:8]
    stream.append({
        "id": thought_id,
        "agent_name": agent_name,
        "message": message,
        "status": status,
        "timestamp": datetime.now().isoformat(),
    })
    _set_thought_stream(tool_context, stream)
    return thought_id


def _complete_tool_thought(
    tool_context: ToolContext,
    thought_id: str,
    message: str,
    status: str = "completed",
) -> None:
    """Internal helper to mark a previously emitted thought as completed."""
    stream = _get_thought_stream(tool_context)
    for thought in stream:
        if thought["id"] == thought_id:
            thought["status"] = status
            thought["message"] = message
            break
    _set_thought_stream(tool_context, stream)
