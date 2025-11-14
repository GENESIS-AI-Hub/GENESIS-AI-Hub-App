from google.adk.agents import Agent
import os
from dotenv import load_dotenv

# --- FIX ---
# Get the directory of this file (chris/agent.py)
current_dir = os.path.dirname(__file__)
# Go one level up to the 'orchestrator' folder
parent_dir = os.path.join(current_dir, '..')
# Specify the full path to the .env file
env_path = os.path.join(parent_dir, '.env')

# Load the .env file from that specific path
load_dotenv(dotenv_path=env_path)
# --- END FIX ---

chris_agent = Agent(
    name="chris",
    model=os.environ.get("CHRIS_MODEL"),
    description="An agent that classifies the tone of a text...",
    instruction=(
        "Given a text, classify its tone..."
    ),
)