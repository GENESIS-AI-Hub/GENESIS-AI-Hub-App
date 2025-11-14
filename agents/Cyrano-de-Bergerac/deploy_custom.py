import vertexai
from vertexai.preview import reasoning_engines
import os

# 1. Hardcode the correct project and bucket
PROJECT_ID = "genesis-hub-osu-test"
LOCATION = "us-west1"
STAGING_BUCKET = "gs://genesis-hub-osu-test-staging" 

print(f"Deploying to {PROJECT_ID} in {LOCATION}...")

# 2. Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# 3. Import your wrapper class
from orchestrator.agent import root_agent

# 4. Deploy the Agent directly
print("Creating Reasoning Engine...")
remote_agent = reasoning_engines.ReasoningEngine.create(
    root_agent,
    requirements=[
        "google-cloud-aiplatform",
        "google-adk[a2a]",
        "pandas",
        "python-dotenv"
    ],
    extra_packages=["orchestrator"],
    
    display_name="Cyrano-Genesis-Hub-Deploy",
)

print("\nDeployment Complete!")
print(f"Reasoning Engine Name: {remote_agent.resource_name}")