# A2A Integration - Technical Implementation

Technical overview of A2A (Agent-to-Agent) integration in OSU Genesis AI Hub.

## Architecture

```
User Browser (Chat UI)
    ↓ HTTP/WebSocket
OSU Genesis AI Hub Backend (FastAPI)
    ↓ JSON-RPC 2.0
External A2A Agent
```

**Components:**
- Model registry: Treats agents as selectable models
- Agent router: Handles agent CRUD and messaging
- Config endpoints: Admin settings for agent connections
- Chat completion: Routes messages to agents via A2A protocol
- Database: Persists agent metadata

## Critical Bug Fix

**Issue:** Agents not appearing in model list after registration

**Root Cause:** Early return in `get_all_models()` at line 67-68:
```python
if len(models) == 0:
    return []  # ← Prevented A2A agents from being added
```

**Solution:** Removed early return, allowing function to continue and add A2A agents from database.

**Impact:** Without this fix, A2A integration was non-functional. Chat completions failed with "Model not found" error.

## Implementation Details

### 1. Database Layer

**File:** `backend/open_webui/models/agents.py`

SQLAlchemy ORM for agent persistence:

```python
class Agent(Base):
    __tablename__ = "agent"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    url = Column(String, nullable=False)
    version = Column(String)
    capabilities = Column(JSON)
    is_active = Column(Boolean, default=True)
    user_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

CRUD operations via `AgentsTable` class:
- `insert_new_agent()` - Create/update agent
- `get_agents()` - Retrieve all active agents
- `get_agent_by_id()` - Get specific agent
- `update_agent_by_id()` - Update agent
- `delete_agent_by_id()` - Soft delete

**Migration:** `backend/open_webui/migrations/versions/XXX_add_agents_table.py`

### 2. API Endpoints

**File:** `backend/open_webui/routers/agents.py`

Agent management REST API:

```
POST   /api/v1/agents/register              - Manual registration
POST   /api/v1/agents/register-by-url       - Auto-register from .well-known/agent.json
GET    /api/v1/agents                       - List all agents
GET    /api/v1/agents/{agent_id}           - Get agent details
PATCH  /api/v1/agents/{agent_id}           - Update agent
DELETE /api/v1/agents/{agent_id}           - Delete agent
POST   /api/v1/agents/{agent_id}/message   - Send A2A message
```

**File:** `backend/open_webui/routers/configs.py`

Admin configuration API:

```
GET    /api/v1/configs/a2a_agents          - Get config
POST   /api/v1/configs/a2a_agents          - Set config + sync to DB
POST   /api/v1/configs/a2a_agents/verify   - Verify connection
```

**Key Change:** Added cache refresh in `set_a2a_agents_config()`:
```python
await get_all_models(request, user=user)  # Proactive cache refresh
```

### 3. Model Registry

**File:** `backend/open_webui/utils/models.py`

**Critical Fix:**
```python
# BEFORE (broken):
if len(models) == 0:
    return []

# AFTER (fixed):
# Removed early return - continue to add A2A agents
```

**A2A Agent Aggregation (lines 229-268):**
```python
# Fetch agents from database
agents = Agents.get_agents()

# Convert each agent to model format
for agent in agents:
    model_id = f"a2a-agent-{agent.id}"
    model = {
        "id": model_id,
        "name": agent.name,
        "object": "model",
        "created": int(agent.created_at.timestamp()),
        "owned_by": "a2a-agent",
        "info": {
            "base_model_id": None,
            "params": {
                "endpoint": agent.endpoint,
                "url": agent.url,
                "version": agent.version,
                "capabilities": agent.capabilities
            }
        }
    }
    models.append(model)

# Cache models in request state
request.app.state.MODELS = models
return models
```

**Logging:** Added `[MODELS]` prefix for debugging.

### 4. Chat Completion

**File:** `backend/open_webui/main.py`

**Reactive Cache Refresh (lines 1145-1150):**
```python
available_models = request.app.state.MODELS.get("data", [])
if not any(m["id"] == form_data.model for m in available_models):
    log.info(f"[CHAT] Model not in cache, refreshing...")
    await get_all_models(request, user=user)
    available_models = request.app.state.MODELS.get("data", [])
```

**Agent Detection:**
```python
if form_data.model.startswith("a2a-agent-"):
    return await generate_a2a_agent_chat_completion(form_data, user)
```

**File:** `backend/open_webui/utils/chat.py`

A2A chat completion handler:

```python
async def generate_a2a_agent_chat_completion(form_data, user):
    # Extract agent ID
    agent_id = form_data.model.replace("a2a-agent-", "")
    agent = Agents.get_agent_by_id(agent_id)
    
    # Format JSON-RPC request
    last_message = form_data.messages[-1]
    json_rpc_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "messageId": str(uuid.uuid4()),
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": last_message.role,
                "parts": [{"text": last_message.content}]
            }
        },
        "id": 1
    }
    
    # Send to agent
    response = requests.post(agent.url, json=json_rpc_request, timeout=60)
    response.raise_for_status()
    
    # Parse response with fallbacks
    data = response.json()
    
    # Try result.artifacts[0].parts[0].text
    content = data.get("result", {}).get("artifacts", [{}])[0].get("parts", [{}])[0].get("text")
    
    # Fallback: result.message.parts[0].text
    if not content:
        content = data.get("result", {}).get("message", {}).get("parts", [{}])[0].get("text")
    
    # Fallback: result directly
    if not content:
        content = data.get("result", {}).get("text", str(data.get("result")))
    
    # Stream response
    return StreamingResponse(
        iter([f"data: {json.dumps({'choices': [{'delta': {'content': content}}]})}\n\n"]),
        media_type="text/event-stream"
    )
```

### 5. Frontend UI

**File:** `src/lib/components/admin/Settings/Connections/AgentConnection.svelte`

Admin UI component for A2A agent management:

**Features:**
- Enable/disable toggle
- Agent connection list
- Add/edit/delete agent connections
- Verify connection button (fetches `.well-known/agent.json`)
- Auto-save on changes

**API Integration:**
```typescript
import { getA2AAgentsConfig, setA2AAgentsConfig, verifyA2AAgent } from '$lib/apis/configs'
```

**File:** `src/lib/components/admin/Settings/Connections.svelte`

Added A2A Agents section to main Connections settings page.

**File:** `src/lib/apis/configs/index.ts`

Frontend API functions:
```typescript
export const getA2AAgentsConfig = async (token: string) => { ... }
export const setA2AAgentsConfig = async (token: string, config: object) => { ... }
export const verifyA2AAgent = async (token: string, connection: object) => { ... }
```

### 6. Testing

**File:** `test_a2a_integration.py`

End-to-end integration test:

**Test Steps:**
1. Verify OSU Genesis AI Hub connection
2. Fetch agent discovery document
3. Configure A2A agents via API
4. Wait for model list refresh
5. Find agent in model list (by URL endpoint match)
6. Send test message via chat completion
7. Validate response

**Smart Agent Selection:**
```python
# Match agent by endpoint URL
agent_model = next(
    (m for m in agent_models if agent_url in m.get("info", {}).get("params", {}).get("url", "")),
    agent_models[0] if agent_models else None
)
```

**Run Command:**
```bash
python test_a2a_integration.py \
  --agent-url http://localhost:8001 \
  --openwebui-url http://localhost:8080 \
  --api-key YOUR_API_KEY \
  --agent-name "Test Agent"
```

## Dual Cache Refresh Strategy

**Problem:** Models cache not updated after agent registration.

**Solution:** Two-level refresh:

1. **Proactive** (configs.py): Refresh immediately after registration
2. **Reactive** (main.py): Refresh on-demand if model not found

This ensures agents are always available without requiring page refresh.

## Protocol Details

### A2A Discovery

**Endpoint:** `/.well-known/agent.json`

**Expected Response:**
```json
{
  "name": "Agent Name",
  "version": "1.0.0",
  "description": "Agent description",
  "capabilities": ["text", "image"],
  "endpoint": "/"
}
```

### A2A Message Format

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "messageId": "uuid",
    "message": {
      "messageId": "uuid",
      "role": "user",
      "parts": [
        {
          "text": "User message"
        }
      ]
    }
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "artifacts": [
      {
        "parts": [
          {
            "text": "Agent response"
          }
        ]
      }
    ]
  },
  "id": 1
}
```

## Logging

Added structured logging throughout:

**Prefixes:**
- `[MODELS]` - Model registry operations
- `[CHAT]` - Chat completion routing
- `[CONFIG]` - Configuration changes
- `[A2A]` - Agent communication

**Examples:**
```
[MODELS] Starting model aggregation
[MODELS] Fetched 2 A2A agents from database
[MODELS] Available models in cache: 2
[CHAT] Routing to A2A agent: a2a-agent-123
[CONFIG] Registered new A2A agent: Test Agent
```

## Files Changed Summary

**New Files (7):**
- `backend/open_webui/models/agents.py`
- `backend/open_webui/routers/agents.py`
- `backend/open_webui/migrations/versions/XXX_add_agents_table.py`
- `src/lib/components/admin/Settings/Connections/AgentConnection.svelte`
- `test_a2a_integration.py`
- `A2A_QUICKSTART.md`
- `A2A_IMPLEMENTATION_SUMMARY.md`

**Modified Files (6):**
- `backend/open_webui/main.py`
- `backend/open_webui/routers/configs.py`
- `backend/open_webui/utils/models.py`
- `backend/open_webui/utils/chat.py`
- `src/lib/components/admin/Settings/Connections.svelte`
- `src/lib/apis/configs/index.ts`

## Configuration

**Environment Variables:** None required. A2A is configured via admin UI or API.

**Settings Location:** Admin Settings > Connections > A2A Agents

**Database:** SQLite (default) with `agent` table

## Security Considerations

- Agent URLs stored in database
- Admin-only access to agent management
- No authentication forwarding to agents (agents are trusted)
- HTTPS support for production deployments

## Performance

- In-memory model cache: `request.app.state.MODELS`
- Cache invalidation on configuration change
- Lazy loading: Agents fetched from DB only during model aggregation
- No polling: Event-driven updates

## Compatibility

- Requires A2A protocol (JSON-RPC 2.0)
- Tested with Google ADK agents
- Compatible with custom A2A implementations
- Requires `.well-known/agent.json` for auto-discovery

## Future Enhancements

Potential improvements:
- Agent authentication/authorization
- Streaming support for long responses
- Multi-turn conversation context
- Agent capabilities filtering
- Health check monitoring
- Agent metrics/analytics
