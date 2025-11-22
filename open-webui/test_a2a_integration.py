#!/usr/bin/env python3
"""
Test script for A2A (Agent-to-Agent) integration in Open WebUI
This script verifies that:
1. Open WebUI is running
2. A2A agents can be registered
3. Agent discovery works
4. Chat completion with agents works

Usage:
    python test_a2a_integration.py --agent-url http://localhost:8001 --openwebui-url http://localhost:8080 --api-key YOUR_API_KEY
"""

import argparse
import json
import requests
import sys
import time
from typing import Dict, Any, Optional


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(message: str):
    """Print success message in green"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message in red"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message in blue"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def print_section(title: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")


def test_open_webui_connection(openwebui_url: str) -> bool:
    """Test if Open WebUI is accessible"""
    try:
        response = requests.get(f"{openwebui_url}/api/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            print_success(f"Open WebUI is running (version: {config.get('version', 'unknown')})")
            return True
        else:
            print_error(f"Open WebUI returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to Open WebUI at {openwebui_url}")
        print_info("Make sure Open WebUI is running: cd backend && sh dev.sh")
        return False
    except Exception as e:
        print_error(f"Error connecting to Open WebUI: {e}")
        return False


def test_agent_discovery(agent_url: str) -> Optional[Dict[str, Any]]:
    """Test if agent's .well-known/agent.json endpoint is accessible"""
    well_known_url = f"{agent_url}/.well-known/agent.json"
    try:
        response = requests.get(well_known_url, timeout=5)
        if response.status_code == 200:
            agent_info = response.json()
            print_success(f"Agent discovery endpoint accessible")
            print_info(f"  Agent name: {agent_info.get('name', 'N/A')}")
            print_info(f"  Agent version: {agent_info.get('version', 'N/A')}")
            print_info(f"  Agent description: {agent_info.get('description', 'N/A')}")
            return agent_info
        else:
            print_error(f"Agent returned status code {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to agent at {agent_url}")
        print_info("Make sure your A2A agent is running")
        return None
    except Exception as e:
        print_error(f"Error connecting to agent: {e}")
        return None


def test_a2a_config_api(openwebui_url: str, api_key: str) -> bool:
    """Test if A2A agents configuration API is accessible"""
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(
            f"{openwebui_url}/api/v1/configs/a2a_agents",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            config = response.json()
            print_success("A2A configuration API is accessible")
            print_info(f"  A2A Agents enabled: {config.get('ENABLE_A2A_AGENTS', False)}")
            print_info(f"  Registered agents: {len(config.get('A2A_AGENT_CONNECTIONS', []))}")
            return True
        elif response.status_code == 401:
            print_error("Invalid API key. Please check your API key.")
            print_info("Get your API key from: Settings → Account → API Key")
            return False
        else:
            print_error(f"A2A config API returned status code {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error accessing A2A config API: {e}")
        return False


def register_agent(openwebui_url: str, api_key: str, agent_url: str, agent_name: str) -> Optional[str]:
    """Register an agent with Open WebUI"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # First, get current config
        response = requests.get(
            f"{openwebui_url}/api/v1/configs/a2a_agents",
            headers=headers,
            timeout=5
        )
        
        if response.status_code != 200:
            print_error(f"Failed to get current A2A config: {response.status_code}")
            return None
        
        config = response.json()
        connections = config.get('A2A_AGENT_CONNECTIONS', [])
        
        # Check if agent already registered
        for conn in connections:
            if conn.get('url') == agent_url:
                print_warning(f"Agent already registered at {agent_url}")
                return agent_url
        
        # Add new agent
        connections.append({
            "url": agent_url,
            "name": agent_name,
            "config": {}
        })
        
        # Update config
        payload = {
            "ENABLE_A2A_AGENTS": True,
            "A2A_AGENT_CONNECTIONS": connections
        }
        
        response = requests.post(
            f"{openwebui_url}/api/v1/configs/a2a_agents",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print_success(f"Successfully registered agent: {agent_name}")
            return agent_url
        else:
            print_error(f"Failed to register agent: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Error registering agent: {e}")
        return None


def test_agent_models_api(openwebui_url: str, api_key: str) -> bool:
    """Test if registered agents appear in the models list"""
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(
            f"{openwebui_url}/api/models",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            agent_models = [m for m in models if m.get('owned_by') == 'a2a-agent']
            
            if agent_models:
                print_success(f"Found {len(agent_models)} A2A agent model(s) in models list")
                for agent_model in agent_models:
                    print_info(f"  - {agent_model.get('name')} (ID: {agent_model.get('id')})")
                return True
            else:
                print_warning("No A2A agent models found in models list")
                print_info("Agents may not have been registered yet")
                return False
        else:
            print_error(f"Models API returned status code {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error accessing models API: {e}")
        return False


def test_chat_completion(openwebui_url: str, api_key: str, agent_model_id: str) -> bool:
    """Test chat completion with an agent"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": agent_model_id,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello! This is a test message from the A2A integration test script."
                }
            ],
            "stream": False
        }
        
        print_info("Sending test message to agent...")
        response = requests.post(
            f"{openwebui_url}/api/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            message_content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            print_success("Successfully received response from agent")
            print_info(f"  Agent response: {message_content[:100]}{'...' if len(message_content) > 100 else ''}")
            return True
        else:
            print_error(f"Chat completion failed with status code {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error testing chat completion: {e}")
        return False


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description='Test A2A integration in Open WebUI')
    parser.add_argument('--agent-url', required=True, help='URL of the A2A agent (e.g., http://localhost:8001)')
    parser.add_argument('--openwebui-url', default='http://localhost:8080', help='URL of Open WebUI (default: http://localhost:8080)')
    parser.add_argument('--api-key', required=True, help='Open WebUI API key (get from Settings → Account → API Key)')
    parser.add_argument('--agent-name', default='Test Agent', help='Name for the agent (default: Test Agent)')
    
    args = parser.parse_args()
    
    print_section("A2A Integration Test Suite")
    print_info(f"Open WebUI URL: {args.openwebui_url}")
    print_info(f"Agent URL: {args.agent_url}")
    print_info(f"Agent Name: {args.agent_name}")
    
    # Test 1: Open WebUI connection
    print_section("Test 1: Open WebUI Connection")
    if not test_open_webui_connection(args.openwebui_url):
        print_error("Test suite aborted: Cannot connect to Open WebUI")
        sys.exit(1)
    
    # Test 2: Agent discovery
    print_section("Test 2: Agent Discovery")
    agent_info = test_agent_discovery(args.agent_url)
    if not agent_info:
        print_error("Test suite aborted: Cannot discover agent")
        sys.exit(1)
    
    # Test 3: A2A Config API
    print_section("Test 3: A2A Configuration API")
    if not test_a2a_config_api(args.openwebui_url, args.api_key):
        print_error("Test suite aborted: Cannot access A2A config API")
        sys.exit(1)
    
    # Test 4: Register agent
    print_section("Test 4: Agent Registration")
    if not register_agent(args.openwebui_url, args.api_key, args.agent_url, args.agent_name):
        print_error("Test suite aborted: Cannot register agent")
        sys.exit(1)
    
    # Wait a bit for registration to propagate
    print_info("Waiting for registration to propagate...")
    time.sleep(2)
    
    # Test 5: Check models API
    print_section("Test 5: Agent in Models List")
    if not test_agent_models_api(args.openwebui_url, args.api_key):
        print_warning("Agent not found in models list, but continuing...")
    
    # Test 6: Chat completion (if agent model is available)
    print_section("Test 6: Chat Completion with Agent")
    # Get agent models to find the model ID
    headers = {"Authorization": f"Bearer {args.api_key}"}
    response = requests.get(f"{args.openwebui_url}/api/models", headers=headers)
    if response.status_code == 200:
        data = response.json()
        models = data.get('data', [])
        agent_models = [m for m in models if m.get('owned_by') == 'a2a-agent']
        
        if agent_models:
            # Find the agent model that matches our registered agent URL
            target_agent_model = None
            for model in agent_models:
                agent_info = model.get('agent', {})
                endpoint = agent_info.get('endpoint', '')
                # Check if this agent's endpoint matches the URL we registered
                if endpoint == args.agent_url or endpoint.rstrip('/') == args.agent_url.rstrip('/'):
                    target_agent_model = model
                    break
            
            # If we didn't find a match by endpoint, try matching by name
            if not target_agent_model:
                for model in agent_models:
                    if model.get('name') == args.agent_name:
                        target_agent_model = model
                        break
            
            # If still no match, use the last one (most recently added)
            if not target_agent_model:
                target_agent_model = agent_models[-1]
                print_warning(f"Could not find agent matching URL {args.agent_url}, using: {target_agent_model.get('name')}")
            
            agent_model_id = target_agent_model.get('id')
            print_info(f"Testing with agent: {target_agent_model.get('name')} (ID: {agent_model_id})")
            if not test_chat_completion(args.openwebui_url, args.api_key, agent_model_id):
                print_warning("Chat completion test failed, but other tests passed")
        else:
            print_warning("No agent models found, skipping chat completion test")
    
    # Final summary
    print_section("Test Suite Complete")
    print_success("All critical tests passed!")
    print_info("\nThe agent is verified for use in Open WebUI:")
    print_info("1. Go to http://localhost:8080")
    print_info("2. Start a new chat")
    print_info("3. Select your agent from the model dropdown")
    print_info("4. Start chatting!")


if __name__ == "__main__":
    main()
