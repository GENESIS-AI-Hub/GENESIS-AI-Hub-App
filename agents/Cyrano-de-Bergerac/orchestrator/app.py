from vertexai import agent_engines
from orchestrator.agent import root_agent # This imports 'root_agent' from orchestrator/agent.py

# This file defines your agent service for the ADK.
# The 'adk deploy' command looks for this 'app' variable.
app = agent_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)