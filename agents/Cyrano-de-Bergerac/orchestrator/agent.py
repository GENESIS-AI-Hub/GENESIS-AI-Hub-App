# We can import the CLASS globally, but NOT the agent instances
from google.adk.agents import SequentialAgent

class OrchestratorApp:
    def __init__(self):
        # --- LAZY IMPORTS ---
        # Move these imports INSIDE the function.
        # This prevents the deployment tool from seeing 'chris_agent' 
        # and 'cyrano_agent' as global variables.
        from .chris.agent import chris_agent
        from .cyrano.agent import cyrano_agent

        # Define the internal agent here
        self.agent = SequentialAgent(
            name="Orchestrator_Agent",
            sub_agents=[
                chris_agent,
                cyrano_agent,
            ]
        )

    # The prompt argument matches your curl command
    def query(self, prompt: str):
        return self.agent.invoke(input=prompt)

# This is now the ONLY instance variable in the whole file
root_agent = OrchestratorApp()