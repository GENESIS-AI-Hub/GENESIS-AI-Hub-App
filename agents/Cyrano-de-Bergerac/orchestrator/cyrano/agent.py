from google.adk.agents import Agent
import os
from dotenv import load_dotenv

# --- FIX ---
# Get the directory of this file (cyrano/agent.py)
current_dir = os.path.dirname(__file__)
# Go one level up to the 'orchestrator' folder
parent_dir = os.path.join(current_dir, '..')
# Specify the full path to the .env file
env_path = os.path.join(parent_dir, '.env')

# Load the .env file from that specific path
load_dotenv(dotenv_path=env_path)
# --- END FIX ---

cyrano_agent = Agent(
    name="cyrano",
    model=os.environ.get("CYRANO_MODEL"),
    description="An agent that rewrites text...",
    instruction=(
        "Rewrite the 'original_payload' to match the given 'tone'..."
    ),
)