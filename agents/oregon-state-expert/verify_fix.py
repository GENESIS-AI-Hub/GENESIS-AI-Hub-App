
import os
from urllib.parse import urlparse
from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Mock Agent
class MockAgent:
    pass

root_agent = MockAgent()

# Test Case 1: APP_URL is set
os.environ["APP_URL"] = "https://oregon-state-expert-525547914539.us-west1.run.app"
app_url = os.environ.get("APP_URL")

print(f"Testing with APP_URL: {app_url}")

if app_url:
    parsed_url = urlparse(app_url)
    print(f"Parsed: host={parsed_url.hostname}, port={parsed_url.port}, scheme={parsed_url.scheme}")
    
    # Simulate to_a2a logic (since we can't easily inspect the resulting Starlette app's internal state without running it, 
    # we'll just print what we would pass to it)
    
    host = parsed_url.hostname
    port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
    protocol = parsed_url.scheme or "http"
    
    print(f"Calling to_a2a with: host='{host}', port={port}, protocol='{protocol}'")
    
    expected_url = f"{protocol}://{host}:{port}"
    print(f"Expected URL (approx): {expected_url}")

# Test Case 2: APP_URL with port
os.environ["APP_URL"] = "http://localhost:8080"
app_url = os.environ.get("APP_URL")
print(f"\nTesting with APP_URL: {app_url}")

if app_url:
    parsed_url = urlparse(app_url)
    host = parsed_url.hostname
    port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
    protocol = parsed_url.scheme or "http"
    print(f"Calling to_a2a with: host='{host}', port={port}, protocol='{protocol}'")
