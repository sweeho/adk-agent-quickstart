import json

from google.adk.tools import ToolContext
from adk_web_agent.tools.thought_tools import _emit_tool_thought, _complete_tool_thought


def format_report(content: str, tool_context: ToolContext, format_type: str = "summary") -> str:
    """Format content into a well-structured report.

    Args:
        content: The raw content to format into a report.
        tool_context: The tool context for accessing shared state.
        format_type: The report format - 'summary', 'detailed', or 'bullet_points'.

    Returns:
        A JSON string with the formatted report.
    """
    # Emit "running" thought
    thought_id = _emit_tool_thought(
        tool_context, "summary_agent",
        f"Formatting report ({format_type} format)..."
    )

    report = {
        "format": format_type,
        "formatted_content": content,
        "sections_generated": 3,
        "word_count": len(content.split()),
        "readability_score": "high",
    }

    # Emit "completed" thought
    _complete_tool_thought(
        tool_context, thought_id,
        f"Report formatted — {report['word_count']} words, {report['sections_generated']} sections"
    )

    return json.dumps(report, indent=2)


def extract_key_points(text: str, tool_context: ToolContext, max_points: int = 5) -> str:
    """Extract key points from a piece of text.

    Args:
        text: The text to extract key points from.
        tool_context: The tool context for accessing shared state.
        max_points: Maximum number of key points to extract.

    Returns:
        A JSON string with extracted key points.
    """
    # Emit "running" thought
    thought_id = _emit_tool_thought(
        tool_context, "summary_agent",
        "Extracting key points from content..."
    )

    result = {
        "source_length": len(text),
        "key_points_extracted": min(max_points, 5),
        "key_points": [
            "The core topic centers around the user's primary question.",
            "Multiple data sources corroborate the main findings.",
            "Analysis reveals actionable insights for the user.",
            "Supporting evidence strengthens the conclusions.",
            "Next steps are clearly defined based on the findings.",
        ][:max_points],
        "summary": f"Extracted {min(max_points, 5)} key points from the provided content covering the main themes and actionable insights.",
    }

    # Emit "completed" thought
    _complete_tool_thought(
        tool_context, thought_id,
        f"Key points extracted — {result['key_points_extracted']} points identified"
    )

    return json.dumps(result, indent=2)
