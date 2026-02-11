# Agent Studio - ADK Backend

## Architecture
Multi-agent orchestration using Google ADK:
- **Root Agent** (Orchestrator) - coordinates sub-agents
- **Research Agent** - searches knowledge bases and web
- **Analysis Agent** - analyzes data, calculates metrics
- **Summary Agent** - formats reports, extracts key points

## Pre-Requisites
1. uv
2. npm

## Setup Google Gemini API Key
1. Open terminal 1
2. Change directory `cd adk-agent-quickstart`
3. Create .env file from example `cp adk_web_agent/.env.example adk_web_agent/.env`
4. Edit `.env` and provide the Google Gemini API key.

## Starting ADK Agent
1. Open terminal 1
2. Change directory `cd adk-agent-quickstart`
3. Execute `uv run python -m adk_web_agent.agent`

## Starting CopilotKit App
1. Open terminal 2
2. Change directory `cd copilotkit-app-quickstart`
3. Execute `npm run dev`

## Launch Chatbot in Browser
1. Open in chrome browser http://localhost:3000