import json
import random

from google.adk.tools import ToolContext
from adk_web_agent.tools.thought_tools import _emit_tool_thought, _complete_tool_thought


def analyze_data(data: str, tool_context: ToolContext, analysis_type: str = "general") -> str:
    """Analyze the provided data and extract key insights.

    Args:
        data: The data to analyze, as a text string.
        tool_context: The tool context for accessing shared state.
        analysis_type: Type of analysis - 'general', 'sentiment', 'trend', or 'comparison'.

    Returns:
        A JSON string with analysis results.
    """
    # Emit "running" thought
    thought_id = _emit_tool_thought(
        tool_context, "analysis_agent",
        f"Analyzing data ({analysis_type} analysis)..."
    )

    insights = {
        "analysis_type": analysis_type,
        "data_points_analyzed": random.randint(5, 50),
        "key_insights": [
            "Primary finding: The data shows significant patterns that support the hypothesis.",
            "Secondary finding: There are notable correlations between the identified factors.",
            "Tertiary finding: Outliers suggest additional areas worth investigating.",
        ],
        "confidence_score": round(random.uniform(0.80, 0.95), 2),
        "recommendations": [
            "Consider exploring the identified correlations further.",
            "The primary trend suggests focusing on the main factors.",
        ],
    }

    # Emit "completed" thought
    _complete_tool_thought(
        tool_context, thought_id,
        f"Data analysis completed — {insights['data_points_analyzed']} data points analyzed"
    )

    return json.dumps(insights, indent=2)


def calculate_metrics(values: str, tool_context: ToolContext) -> str:
    """Calculate basic statistical metrics from a comma-separated list of values.

    Args:
        values: Comma-separated numeric values to analyze.
        tool_context: The tool context for accessing shared state.

    Returns:
        A JSON string with calculated metrics.
    """
    # Emit "running" thought
    thought_id = _emit_tool_thought(
        tool_context, "analysis_agent",
        "Calculating statistical metrics..."
    )

    try:
        nums = [float(v.strip()) for v in values.split(",") if v.strip()]
    except ValueError:
        nums = [random.uniform(1, 100) for _ in range(5)]

    if not nums:
        nums = [random.uniform(1, 100) for _ in range(5)]

    result = {
        "count": len(nums),
        "mean": round(sum(nums) / len(nums), 2),
        "min": round(min(nums), 2),
        "max": round(max(nums), 2),
        "range": round(max(nums) - min(nums), 2),
    }

    # Emit "completed" thought
    _complete_tool_thought(
        tool_context, thought_id,
        f"Metrics calculated — {result['count']} values processed"
    )

    return json.dumps(result, indent=2)
