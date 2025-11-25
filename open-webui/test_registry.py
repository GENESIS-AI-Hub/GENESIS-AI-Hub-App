import requests
import uuid
import json

BASE_URL = "http://localhost:8080/api/v1"
# You might need to adjust the token if auth is enabled
TOKEN = "your_token_here" 

def test_registry_flow():
    print("Testing Registry API...")
    
    # 1. Submit an Agent
    # We need a valid URL that hosts .well-known/agent.json. 
    # Since we can't easily mock an external server here without setup, 
    # we might fail on the fetch step if we use a dummy URL.
    # However, we can test the validation logic.
    
    print("1. Testing Submission Validation...")
    try:
        res = requests.post(
            f"{BASE_URL}/registry/",
            json={"url": "invalid-url"},
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        print(f"Submission with invalid URL status: {res.status_code}")
        assert res.status_code == 400
    except Exception as e:
        print(f"Submission test failed (expectedly if server not running): {e}")

    # 2. List Agents
    print("2. Testing List Agents...")
    try:
        res = requests.get(
            f"{BASE_URL}/registry/",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        print(f"List agents status: {res.status_code}")
        if res.ok:
            print(f"Agents found: {len(res.json())}")
    except Exception as e:
        print(f"List test failed: {e}")

if __name__ == "__main__":
    test_registry_flow()
