import random
import json

from google.adk.tools import ToolContext
from adk_web_agent.tools.thought_tools import _emit_tool_thought, _complete_tool_thought


def search_knowledge_base(query: str, tool_context: ToolContext) -> str:
    """Search the internal knowledge base for information relevant to the query.

    Args:
        query: The search query to find relevant information.
        tool_context: The tool context for accessing shared state.

    Returns:
        A JSON string with search results.
    """
    # Emit "running" thought
    thought_id = _emit_tool_thought(
        tool_context, "research_agent",
        f"Searching knowledge base for: {query}"
    )

    # Simulated knowledge base results
    results = {
        "query": query,
        "results_found": random.randint(3, 15),
        "sources": ["internal_docs", "faq_database", "product_catalog"],
        "top_results": [
            f"Result 1: Relevant information about '{query}' from internal documentation.",
            f"Result 2: FAQ entry related to '{query}'.",
            f"Result 3: Product details matching '{query}'.",
        ],
        "confidence": round(random.uniform(0.75, 0.98), 2),
    }

    # Emit "completed" thought
    _complete_tool_thought(
        tool_context, thought_id,
        f"Knowledge base search completed — {results['results_found']} results found"
    )

    return json.dumps(results, indent=2)


def web_search(query: str, tool_context: ToolContext) -> str:
    """Search the web for up-to-date information about the query.

    Args:
        query: The search query to look up online.
        tool_context: The tool context for accessing shared state.

    Returns:
        A JSON string with web search results.
    """
    # Emit "running" thought
    thought_id = _emit_tool_thought(
        tool_context, "research_agent",
        f"Searching the web for: {query}"
    )

    results = {
        "query": query,
        "web_results": [
            {"title": f"Latest info on {query}", "snippet": f"Comprehensive overview of {query} with recent updates and analysis.", "url": f"https://example.com/{query.replace(' ', '-')}"},
            {"title": f"{query} - Expert Analysis", "snippet": f"In-depth expert analysis covering key aspects of {query}.", "url": f"https://example.com/analysis/{query.replace(' ', '-')}"},
        ],
        "total_results": random.randint(100, 10000),
    }

    # Emit "completed" thought
    _complete_tool_thought(
        tool_context, thought_id,
        f"Web search completed — {results['total_results']} results found"
    )

    return json.dumps(results, indent=2)
