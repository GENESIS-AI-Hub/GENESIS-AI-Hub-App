from vertexai import agent_engines
from orchestrator.agent import root_agent # modify this if your agent is not in agent.py

app = agent_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

# adk deploy agent_engine --project=cyrano-de-bergerac-468215 --region=us-west1 --staging_bucket=gs://cyrano-staging-bucket --display_name=cyrando-de-bergerac-agent-orchestrator orchestrator