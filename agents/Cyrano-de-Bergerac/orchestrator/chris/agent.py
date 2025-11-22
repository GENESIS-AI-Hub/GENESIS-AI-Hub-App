from google.adk.agents import Agent
import os
from dotenv import load_dotenv

load_dotenv()

chris_agent = Agent(
    name="chris",
    # model=os.environ.get("CHRIS_MODEL"),
    model="gemini-1.5-pro-latest",
    description="An agent that classifies the tone of a text and prepares the data for the Cyrano agent.",
    instruction=(
        "Given a text, classify its tone (e.g., formal, informal, angry, happy). "
        "Then, output a JSON string with two keys: 'original_payload' (the original text) and 'tone' (the classified tone)."
    ),
)
