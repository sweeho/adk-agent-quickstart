"""Middleware callbacks for capturing Gemini thought summaries and tracking agent delegation.

These callbacks are attached to all LlmAgents to:
1. Extract thought summary parts (part.thought == True) from Gemini responses
2. Track which agent (root or sub-agent) is currently handling the work
3. Inject both into the agent session state so they propagate via AG-UI to the frontend
"""

import uuid
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short_id() -> str:
    return str(uuid.uuid4())[:8]


# ---------------------------------------------------------------------------
# Agent delegation tracking
# ---------------------------------------------------------------------------

def before_agent_callback(callback_context):
    """Track which agent is currently handling the work.

    Called when an agent (root or sub) begins processing.
    Pushes the agent name onto the delegation chain.
    """
    chain = list(callback_context.state.get("delegation_chain", []))
    agent_name = callback_context.agent_name
    chain.append(agent_name)
    callback_context.state["delegation_chain"] = chain
    callback_context.state["delegated_agent"] = agent_name


def after_agent_callback(callback_context):
    """Pop agent from delegation chain when it finishes.

    Restores the delegated_agent to the parent (or root_agent if empty).
    """
    chain = list(callback_context.state.get("delegation_chain", []))
    agent_name = callback_context.agent_name
    if chain and chain[-1] == agent_name:
        chain.pop()
    callback_context.state["delegation_chain"] = chain
    callback_context.state["delegated_agent"] = chain[-1] if chain else "root_agent"


# ---------------------------------------------------------------------------
# Thought summary extraction
# ---------------------------------------------------------------------------

def after_model_callback(callback_context, llm_response):
    """Extract Gemini thought summary from LLM response parts.

    When include_thoughts=True is set in ThinkingConfig, Gemini returns
    parts with thought=True containing summarized versions of internal
    reasoning.  We extract these and inject them into the session state
    so the frontend can display them.

    CRITICAL: We return the response unchanged to preserve thought
    signatures required for function calling in Gemini 3 models.
    """
    if llm_response.content is None or llm_response.content.parts is None:
        return llm_response  # Nothing to extract

    thought_parts = []
    for part in llm_response.content.parts:
        if hasattr(part, "thought") and part.thought and part.text:
            thought_parts.append(part.text)

    if thought_parts:
        # Join multiple thought parts (rare but possible)
        thought_summary = "\n".join(thought_parts)
        agent_name = callback_context.agent_name

        # Set the latest thought summary in state (overwritten per turn)
        callback_context.state["thought_summary"] = thought_summary
        callback_context.state["thought_summary_agent"] = agent_name

        # Also append to the thought_stream for timeline display
        stream = list(callback_context.state.get("thought_stream", []))
        stream.append({
            "id": _short_id(),
            "agent_name": agent_name,
            "message": thought_summary,
            "status": "completed",
            "timestamp": _now_iso(),
            "is_thought_summary": True,
        })
        # Cap stream size
        if len(stream) > 100:
            stream = stream[-100:]
        callback_context.state["thought_stream"] = stream

    # Extract thinking token count if available
    if llm_response.usage_metadata:
        thoughts_tokens = getattr(llm_response.usage_metadata, "thoughts_token_count", None)
        if thoughts_tokens is not None:
            prev = callback_context.state.get("thinking_tokens_total", 0)
            callback_context.state["thinking_tokens_total"] = prev + thoughts_tokens

    # CRITICAL: Return unchanged to preserve thought signatures
    return llm_response
