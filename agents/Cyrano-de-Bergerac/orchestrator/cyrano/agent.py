
from google.adk.agents import Agent
import os
from dotenv import load_dotenv

load_dotenv()

cyrano_agent = Agent(
    name="cyrano",
    # model=os.environ.get("CYRANO_MODEL"),
    model="gemini-1.5-pro-latest",
    description="An agent that crafts a reply to a message in a specific tone.",
    instruction=(
        "You will receive a JSON string containing 'original_payload' and 'tone'. "
        "Craft an eloquent reply to the 'original_payload' in the given 'tone'."
    ),
)
