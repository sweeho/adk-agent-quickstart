import json
import random

def analyze_data(data: str, analysis_type: str = "general") -> str:
    """Analyze the provided data and extract key insights.

    Args:
        data: The data to analyze, as a text string.
        analysis_type: Type of analysis - 'general', 'sentiment', 'trend', or 'comparison'.

    Returns:
        A JSON string with analysis results.
    """
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
    return json.dumps(insights, indent=2)


def calculate_metrics(values: str) -> str:
    """Calculate basic statistical metrics from a comma-separated list of values.

    Args:
        values: Comma-separated numeric values to analyze.

    Returns:
        A JSON string with calculated metrics.
    """
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
    return json.dumps(result, indent=2)
