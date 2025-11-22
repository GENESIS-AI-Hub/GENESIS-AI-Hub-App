# A2A Agent Integration - Quick Start Guide

This guide provides setup instructions for using A2A (Agent-to-Agent) agents with Open WebUI.

## Overview

A2A integration enables Open WebUI to communicate with external AI agents using the A2A protocol (JSON-RPC 2.0). Agents appear as selectable models in the chat interface.

## Prerequisites

- Open WebUI v0.6.5 or later
- An A2A-compatible agent running
- Admin access to Open WebUI

## Setup

### 1. Start Your A2A Agent

```bash
# Example: Starting a Google ADK agent
cd /path/to/your/agent
source .venv/bin/activate
uvicorn orchestrator.agent:a2a_app --host localhost --port 8001
```

Verify the agent is running:
```bash
curl http://localhost:8001/.well-known/agent.json
```

### 2. Start Open WebUI

```bash
cd backend
conda activate open-webui
sh dev.sh
```

Access at: http://localhost:8080

### 3. Add Agent in Admin Settings

1. Log in to Open WebUI
2. Navigate to: Settings > Admin Settings > Connections
3. Scroll to **A2A Agents** section
4. Toggle switch to enable A2A agents
5. Click **+** to add a new connection
6. Enter agent URL: `localhost:8001`
7. Click verify button and wait for confirmation
8. Click **Save**

### 4. Use Agent in Chat

1. Start a new chat
2. Select your agent from the model dropdown
3. Send a message
4. Agent will process and respond

## Configuration via API

### Get Current Configuration

```bash
curl -X GET http://localhost:8080/api/v1/configs/a2a_agents \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Add Agent

```bash
curl -X POST http://localhost:8080/api/v1/configs/a2a_agents \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "ENABLE_A2A_AGENTS": true,
    "A2A_AGENT_CONNECTIONS": [
      {
        "url": "http://localhost:8001",
        "name": "My Agent",
        "config": {}
      }
    ]
  }'
```

### Verify Connection

```bash
curl -X POST http://localhost:8080/api/v1/configs/a2a_agents/verify \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:8001",
    "name": "My Agent",
    "config": {}
  }'
```

## Troubleshooting

### Agent Not Appearing in Model List

**Solution:**
- Verify agent connection shows confirmation in settings
- Ensure "A2A Agents" toggle is enabled
- Click Save button
- Refresh browser page
- Check backend logs for `[MODELS]` entries

### Failed to Verify Agent Connection

**Solution:**
- Verify agent is running: `curl http://localhost:8001/.well-known/agent.json`
- Check agent server logs for errors
- For localhost, try both `localhost:8001` and `http://localhost:8001`

### Agent Returns Error in Chat

**Solution:**
- Check agent server logs
- Test agent directly:
  ```bash
  curl -X POST http://localhost:8001 \
    -H "Content-Type: application/json" \
    -d '{
      "jsonrpc": "2.0",
      "method": "message/send",
      "params": {
        "messageId": "test-123",
        "message": {
          "messageId": "test-123",
          "role": "user",
          "parts": [{"text": "Hello"}]
        }
      },
      "id": 1
    }'
  ```
- Check Open WebUI backend logs for errors

## Creating Custom A2A Agents

### Minimum Requirements

1. Expose `.well-known/agent.json` endpoint:
```json
{
  "name": "My Agent",
  "version": "1.0.0",
  "description": "Custom A2A agent",
  "capabilities": ["text"]
}
```

2. Implement JSON-RPC 2.0 endpoint accepting `message/send` method

### Expected Response Format

```json
{
  "jsonrpc": "2.0",
  "result": {
    "artifacts": [
      {
        "parts": [
          {
            "text": "Response text"
          }
        ]
      }
    ]
  },
  "id": 1
}
```

### Python Example

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/.well-known/agent.json")
async def agent_discovery():
    return {
        "name": "My Agent",
        "version": "1.0.0",
        "description": "Custom agent",
        "capabilities": ["text"]
    }

class JSONRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: dict
    id: int

@app.post("/")
async def handle_jsonrpc(request: JSONRPCRequest):
    if request.method == "message/send":
        user_message = request.params["message"]["parts"][0]["text"]
        response_text = f"Echo: {user_message}"
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "artifacts": [{
                    "parts": [{"text": response_text}]
                }]
            },
            "id": request.id
        }
```

Run with: `uvicorn my_agent:app --host localhost --port 8001`

## Automated Testing

```bash
python test_a2a_integration.py \
  --agent-url http://localhost:8001 \
  --openwebui-url http://localhost:8080 \
  --api-key YOUR_API_KEY \
  --agent-name "My Agent"
```

The test verifies:
- Open WebUI connection
- Agent discovery
- Configuration API
- Agent registration
- Model list visibility
- Chat completion

## API Key

To get your API key:
1. Open http://localhost:8080
2. Log in or create account
3. Go to Settings > Account
4. Copy API Key

## Resources

- JSON-RPC 2.0 Spec: https://www.jsonrpc.org/specification
- Google ADK: https://google.github.io/adk-docs/
- Open WebUI: https://github.com/open-webui/open-webui
# Activate agent's environment (if using venv)
source .venv/bin/activate

# Start the A2A server
uvicorn orchestrator.agent:a2a_app --host localhost --port 8001
```

Verify the agent is running:
```bash
curl http://localhost:8001/.well-known/agent-card.json
```

### Step 2: Start Open WebUI

```bash
# Navigate to Open WebUI backend
cd /Users/minsoup/GENESIS-AI-Hub-App/open-webui/backend

# Activate conda environment
conda activate open-webui

# Start the server
sh dev.sh
```

Open your browser to: http://localhost:8080

### Step 3: Add Agent in Settings (Web UI)

1. **Log in to Open WebUI** at http://localhost:8080

2. **Open Admin Settings:**
   - Click your profile icon (top-right)
   - Select **Settings**
   - Go to **Admin Settings** (requires admin role)
   - Click the **Connections** tab

3. **Enable and Add A2A Agent:**
   - Scroll to **A2A Agents** section
   - Toggle the switch to **ON** (enable A2A agents)
   - Click the **+** button to add a new connection

4. **Configure Agent:**
   - **Agent URL**: `localhost:8001` (or your agent's URL)
   - **Agent Name**: Leave blank to auto-detect, or enter custom name
   - Click the **Verify Connection** button (↻ icon)
   - Wait for green checkmark ✓

5. **Save:**
   - Click **Save** button at bottom of page
   - Agent will now appear in model selector!

### Step 4: Use Agent in Chat

1. **Start New Chat:**
   - Return to main chat interface
   - Click **New Chat** button

2. **Select Agent Model:**
   - Click the model dropdown (top of chat)
   - Find your agent (look for `agent` and `a2a` tags)
   - Select the agent

3. **Chat:**
   - Type your message
   - Press Enter or click Send
   - Agent processes and responds!

## Automated Testing

Run the provided test script to verify everything works:

```bash
# Get your API key from: Settings → Account → API Key
export OPENWEBUI_API_KEY="your-api-key-here"

# Run test
python test_a2a_integration.py \
  --agent-url http://localhost:8001 \
  --openwebui-url http://localhost:8080 \
  --api-key $OPENWEBUI_API_KEY \
  --agent-name "Cyrano de Bergerac"
```

The test will verify:
- ✓ Open WebUI is accessible
- ✓ Agent discovery endpoint works
- ✓ A2A configuration API works
- ✓ Agent registration succeeds
- ✓ Agent appears in models list
- ✓ Chat completion works

## Configuration via API (Advanced)

### Get Current Configuration

```bash
curl -X GET http://localhost:8080/api/v1/configs/a2a_agents \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Add Agent via API

```bash
curl -X POST http://localhost:8080/api/v1/configs/a2a_agents \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "ENABLE_A2A_AGENTS": true,
    "A2A_AGENT_CONNECTIONS": [
      {
        "url": "http://localhost:8001",
        "name": "Cyrano de Bergerac",
        "config": {}
      }
    ]
  }'
```

### Verify Agent Connection

```bash
curl -X POST http://localhost:8080/api/v1/configs/a2a_agents/verify \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:8001",
    "name": "Test Agent",
    "config": {}
  }'
```

## Troubleshooting

### Agent Not Appearing in Model List

**Symptoms:** After adding agent in settings, it doesn't show up in model dropdown.

**Solutions:**
1. Verify agent connection has green checkmark in settings
2. Click **Save** button in settings
3. Refresh the browser page (Ctrl+R / Cmd+R)
4. Check that "A2A Agents" toggle is ON
5. Check backend logs for `[MODELS]` entries showing agent was added
6. Look at browser console for errors (F12 → Console)

**Note**: Agents are now automatically added even if you have no OpenAI/Ollama models configured. If you previously experienced this issue, it has been fixed!

### "Failed to Verify Agent Connection"

**Symptoms:** Red X instead of green checkmark when verifying.

**Solutions:**
1. Verify agent is running:
   ```bash
   curl http://localhost:8001/.well-known/agent-card.json
   # or
   curl http://localhost:8001/.well-known/agent.json
   ```

2. Check agent server logs for errors

3. For localhost, try both:
   - `localhost:8001` (auto-detects http://)
   - `http://localhost:8001` (explicit)

4. For remote agents, use HTTPS:
   - `https://agent.example.com`

### Agent Responds with Error

**Symptoms:** Agent appears in list but returns errors in chat.

**Solutions:**
1. Check agent server logs during chat attempt

2. Test agent directly with JSON-RPC:
   ```bash
   curl -X POST http://localhost:8001 \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "method": "message/send",
       "params": {
         "messageId": "test-123",
         "message": {
           "messageId": "test-123",
           "role": "user",
           "parts": [{"text": "Hello!"}]
         }
       },
       "id": 1
     }'
   ```

3. Verify agent response format matches A2A spec:
   - Should return JSON-RPC 2.0 response
   - Result should contain `artifacts[].parts[].text`

4. Check Open WebUI backend logs:
   ```bash
   # In terminal running `sh dev.sh`
   # Look for A2A-related errors
   ```

### Streaming Not Working

**Symptoms:** Agent works but responses appear all at once.

**Notes:**
- A2A protocol doesn't inherently support streaming
- Open WebUI simulates streaming by chunking the full response
- This is expected behavior - agent receives and processes full message
- Response is then word-by-word streamed to UI for better UX

## Creating Your Own A2A Agent

To create a custom A2A-compatible agent:

### Minimum Requirements

1. **Expose `.well-known/agent.json` endpoint:**
   ```json
   {
     "name": "My Custom Agent",
     "version": "1.0.0",
     "description": "A custom A2A agent",
     "capabilities": ["text"],
     "skills": []
   }
   ```

2. **Implement JSON-RPC 2.0 endpoint** (root path or `/jsonrpc`):
   - Accept `message/send` method
   - Process user message
   - Return response in A2A format

### Example Response Format

```json
{
  "jsonrpc": "2.0",
  "result": {
    "artifacts": [
      {
        "parts": [
          {
            "text": "Hello! This is my response."
          }
        ]
      }
    ]
  },
  "id": 1
}
```

### Python Example (FastAPI)

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/.well-known/agent.json")
async def agent_discovery():
    return {
        "name": "My Agent",
        "version": "1.0.0",
        "description": "Custom agent",
        "capabilities": ["text"]
    }

class JSONRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: dict
    id: int

@app.post("/")
async def handle_jsonrpc(request: JSONRPCRequest):
    if request.method == "message/send":
        user_message = request.params["message"]["parts"][0]["text"]
        
        # Your agent logic here
        response_text = f"Echo: {user_message}"
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "artifacts": [{
                    "parts": [{"text": response_text}]
                }]
            },
            "id": request.id
        }
```

Run with:
```bash
uvicorn my_agent:app --host localhost --port 8001
```

## Benefits of A2A Integration

1. **Unified Interface**: Users interact with agents through familiar chat UI
2. **No Code Changes**: Add/remove agents without modifying Open WebUI code
3. **Multi-Agent**: Support multiple agents simultaneously
4. **Flexible**: Agents can be local or remote
5. **Standardized**: Uses open JSON-RPC 2.0 and A2A protocols

## Next Steps

- Create custom agents for specialized tasks
- Deploy agents to production environments
- Integrate with external APIs through agents
- Build multi-agent workflows

## Support

For issues or questions:
1. Check Open WebUI logs: Terminal running `sh dev.sh`
2. Check agent logs: Terminal running your agent
3. Review README.md for detailed protocol information
4. Use the test script to diagnose issues

## Resources

- **Google ADK Documentation**: https://google.github.io/adk-docs/
- **A2A Protocol Spec**: Reference Google ADK A2A implementation
- **Open WebUI Docs**: https://docs.openwebui.com/
