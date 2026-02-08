from fastapi import FastAPI, Request
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents import LlmAgent
from google.genai.types import GenerateContentConfig, ThinkingConfig, ThinkingLevel
import os
from dotenv import load_dotenv
import logging

# Enable debug logging for ADK agent
logging.basicConfig(level=logging.DEBUG)

load_dotenv()

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.genai.types import Content, Part
from contextvars import ContextVar

# Context variable to pass request state to callbacks
show_thoughts_var: ContextVar[bool] = ContextVar('show_thoughts', default=False)

async def after_model_callback(ctx: CallbackContext, response: LlmResponse) -> LlmResponse | None:
    """Modify the response to include thoughts in the text if toggle is on."""
    show_thoughts = show_thoughts_var.get()
    logging.info(f"after_model_callback: show_thoughts={show_thoughts}")
    
    if not show_thoughts:
        logging.info("Thoughts disabled, skipping modification")
        return response
    
    if response.candidates:
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                thought_parts = []
                response_parts = []
                
                for part in candidate.content.parts:
                    logging.info(f"Part: text='{part.text[:50] if part.text else None}...', thought={getattr(part, 'thought', None)}")
                    if hasattr(part, 'thought') and part.thought:
                        thought_parts.append(f"💭 **Thinking:** {part.text}")
                    else:
                        response_parts.append(part.text if part.text else "")
                
                if thought_parts:
                    # Combine thoughts and response
                    combined = "\n\n".join(thought_parts) + "\n\n---\n\n" + "".join(response_parts)
                    candidate.content.parts = [Part(text=combined)]
                    logging.info(f"Modified response with {len(thought_parts)} thought parts")
                else:
                    logging.info("No thought parts found")
    return response

agent = LlmAgent(
    name="assistant",
    model="gemini-2.5-flash",
    instruction="Be helpful and fun!",
    generate_content_config=GenerateContentConfig(
        thinking_config=ThinkingConfig(
            include_thoughts=True,
            thinking_budget=1024,  # Increased budget for more thinking
        )
    ),
    after_model_callback=after_model_callback,
)

# For MVP: Use a single ADK agent
# In production, you would create per-user agents or use a database-backed session store
adk_agent = ADKAgent(
    adk_agent=agent,
    app_name="demo_app",
    user_id="shared",  # All users share this for MVP
    session_timeout_seconds=3600,
    use_in_memory_services=True
)

app = FastAPI()

# Middleware to extract show-thoughts header
@app.middleware("http")
async def set_show_thoughts_context(request: Request, call_next):
    show_thoughts = request.headers.get('x-show-thoughts', 'false').lower() == 'true'
    logging.info(f"Request headers: x-show-thoughts={show_thoughts}")
    show_thoughts_var.set(show_thoughts)
    response = await call_next(request)
    return response

# Add the standard ADK endpoint
add_adk_fastapi_endpoint(app, adk_agent, path="/")

# Future endpoint for session management
@app.get("/sessions")
async def list_sessions(username: str):
    """List all sessions for a user"""
    # MVP: Return default session
    # TODO: Implement per-user session tracking
    return {"sessions": ["default"], "username": username}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "ADK agent server is running",
        "thinking_enabled": True,
        "note": "If you hit API quota limits, wait 24 hours or use Vertex AI (set GOOGLE_GENAI_USE_VERTEXAI=1 and configure GCP credentials)"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)