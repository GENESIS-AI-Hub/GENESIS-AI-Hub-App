
from google.adk.agents import SequentialAgent
from chris.agent import chris_agent
from cyrano.agent import cyrano_agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Define the sequential agent
orchestrator = SequentialAgent(
    name="Orchestrator_Agent",
    sub_agents=[
        chris_agent,
        cyrano_agent,
    ]
)

root_agent = orchestrator
a2a_app = to_a2a(root_agent, port=8001)