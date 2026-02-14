from google.adk.agents import LlmAgent
from google.genai import types

from adk_web_agent.tools.research_tools import search_knowledge_base, web_search
from adk_web_agent.tools.analysis_tools import analyze_data, calculate_metrics
from adk_web_agent.tools.summary_tools import format_report, extract_key_points
from adk_web_agent.tools.thought_tools import emit_thought
from adk_web_agent.tools.thinking_middleware import (
    after_model_callback,
    before_agent_callback,
    after_agent_callback,
)

# --- Model & Thinking Configuration ---
MODEL_NAME = "gemini-3-flash-preview"
THINKING_CONFIG = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(
        include_thoughts=True,
        thinking_level="low",
    )
)

# Sub-agent 1: Research Agent
research_agent = LlmAgent(
    name="research_agent",
    model=MODEL_NAME,
    description="Gathers information from knowledge bases and the web. Use this agent when the user asks a question that requires looking up information, facts, or current data.",
    instruction="""You are a Research Agent specializing in information gathering.
Your job is to find relevant information using the tools available to you.

When given a query:
1. First search the internal knowledge base for relevant information.
2. If needed, also perform a web search for up-to-date information.
3. Compile and present all findings clearly.

Always cite your sources and indicate confidence levels.""",
    tools=[search_knowledge_base, web_search],
    generate_content_config=THINKING_CONFIG,
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    after_model_callback=after_model_callback,
)

# Sub-agent 2: Analysis Agent
analysis_agent = LlmAgent(
    name="analysis_agent",
    model=MODEL_NAME,
    description="Analyzes data, identifies patterns, and provides insights. Use this agent when the user needs data analysis, comparisons, trend analysis, or statistical calculations.",
    instruction="""You are an Analysis Agent specializing in data processing and insight extraction.
Your job is to analyze information and provide meaningful insights.

When given data or a question requiring analysis:
1. Determine the appropriate analysis type (general, sentiment, trend, comparison).
2. Use the analyze_data tool to process the information.
3. If numeric data is involved, use calculate_metrics for statistical analysis.
4. Present insights clearly with confidence scores.

Always explain your reasoning and methodology.""",
    tools=[analyze_data, calculate_metrics],
    generate_content_config=THINKING_CONFIG,
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    after_model_callback=after_model_callback,
)

# Sub-agent 3: Summary Agent
summary_agent = LlmAgent(
    name="summary_agent",
    model=MODEL_NAME,
    description="Formats information into clear, well-structured reports and extracts key points. Use this agent when information needs to be organized, summarized, or formatted for presentation.",
    instruction="""You are a Summary Agent specializing in content organization and report generation.
Your job is to take information and present it in a clear, structured format.

When given content to summarize:
1. Extract the key points from the provided information.
2. Format the content into an appropriate report structure.
3. Ensure the output is clear, concise, and well-organized.

Always maintain accuracy while improving readability.""",
    tools=[format_report, extract_key_points],
    generate_content_config=THINKING_CONFIG,
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    after_model_callback=after_model_callback,
)

# Root orchestrator agent with sub-agents
root_agent = LlmAgent(
    model=MODEL_NAME,
    name="root_agent",
    description="Main orchestrator that coordinates research, analysis, and summary agents to provide comprehensive answers.",
    instruction="""You are the Main Orchestrator Agent for Agent Studio, coordinating a team of specialized sub-agents.

Your role is to understand the user's request and delegate to the appropriate sub-agents:

1. **Research Agent** - For gathering information, looking up facts, or finding current data.
2. **Analysis Agent** - For analyzing data, identifying patterns, performing calculations, or comparing options.
3. **Summary Agent** - For organizing, formatting, or summarizing information into clear reports.

Strategy guidelines:
- For simple factual questions: Use the Research Agent.
- For questions requiring analysis: Use Research Agent first, then Analysis Agent.
- For comprehensive requests: Use Research Agent → Analysis Agent → Summary Agent in sequence.
- Always synthesize the results from sub-agents into a clear, helpful final response.

**IMPORTANT - Thought Stream Reporting:**
Before delegating to any sub-agent, you MUST use the emit_thought tool to report your reasoning:
- agent_name: "root_agent"
- message: a brief description of your plan (e.g. "Delegating to Research Agent for information gathering")
- status: "running"

After receiving results from sub-agents, emit a completed thought:
- agent_name: "root_agent"
- message: a brief summary of what was accomplished
- status: "completed"

Be transparent about which agents you're using and why. Provide comprehensive, well-structured answers.""",
    tools=[emit_thought],
    sub_agents=[research_agent, analysis_agent, summary_agent],
    generate_content_config=THINKING_CONFIG,
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    after_model_callback=after_model_callback,
)


# --- FastAPI Server ---
if __name__ == "__main__":
    import logging
    import asyncio
    from contextlib import asynccontextmanager
    from fastapi import FastAPI, Request
    from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
    from dotenv import load_dotenv
    import uvicorn

    from adk_web_agent.database.db import init_db
    from adk_web_agent.routes.auth import router as auth_router
    from adk_web_agent.routes.sessions import router as sessions_router
    from adk_web_agent.routes.admin import router as admin_router

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    load_dotenv()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Initialize database on startup."""
        await init_db()
        yield

    adk_agent = ADKAgent(
        adk_agent=root_agent,
        app_name="agent_studio",
        user_id="demo_user",
        session_timeout_seconds=3600,
        use_in_memory_services=True,
    )

    app = FastAPI(lifespan=lifespan)

    # Include REST API routers
    app.include_router(auth_router)
    app.include_router(sessions_router)
    app.include_router(admin_router)

    # ADK agent endpoint
    add_adk_fastapi_endpoint(app, adk_agent, path="/")

    uvicorn.run(app, host="localhost", port=8000)
