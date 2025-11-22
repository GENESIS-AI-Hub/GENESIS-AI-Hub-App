# A2A Integration - Code Changes

Complete inventory of code modifications for A2A integration.

## New Files

### 1. backend/open_webui/models/agents.py

**Purpose:** Agent database model and CRUD operations

**Key Components:**

```python
class Agent(Base):
    __tablename__ = "agent"
    
    # Primary fields
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    url = Column(String, nullable=False)
    
    # Optional metadata
    version = Column(String)
    description = Column(Text)
    capabilities = Column(JSON)
    skills = Column(JSON)
    
    # Schema definitions
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    default_input_modes = Column(JSON)
    default_output_modes = Column(JSON)
    
    # Status and timestamps
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    user_id = Column(String)

class AgentsTable:
    def insert_new_agent(self, form_data: AgentForm, user_id: str) -> Optional[AgentModel]
    def get_agents(self) -> List[AgentModel]
    def get_agent_by_id(self, agent_id: str) -> Optional[AgentModel]
    def update_agent_by_id(self, agent_id: str, form_data: AgentForm) -> Optional[AgentModel]
    def delete_agent_by_id(self, agent_id: str) -> bool
```

**Lines:** ~250

---

### 2. backend/open_webui/routers/agents.py

**Purpose:** REST API for agent management

**Endpoints:**

```python
@router.post("/register")
async def register_agent(form_data: AgentRegisterForm, user=Depends(get_admin_user))

@router.post("/register-by-url")
async def register_agent_by_url(form_data: AgentUrlForm, user=Depends(get_admin_user))

@router.get("")
async def get_agents(user=Depends(get_current_user))

@router.get("/{agent_id}")
async def get_agent_by_id(agent_id: str, user=Depends(get_current_user))

@router.patch("/{agent_id}")
async def update_agent(agent_id: str, form_data: AgentUpdateForm, user=Depends(get_admin_user))

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, user=Depends(get_admin_user))

@router.post("/{agent_id}/message")
async def send_message_to_agent(agent_id: str, form_data: AgentMessageForm, user=Depends(get_current_user))
```

**Key Functions:**

```python
async def fetch_agent_discovery(url: str) -> dict:
    """Fetch .well-known/agent.json"""
    response = requests.get(f"{url}/.well-known/agent.json", timeout=10)
    return response.json()

async def send_a2a_message(agent_url: str, message: dict) -> dict:
    """Send JSON-RPC 2.0 message"""
    json_rpc_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {"messageId": str(uuid.uuid4()), "message": message},
        "id": 1
    }
    response = requests.post(agent_url, json=json_rpc_request, timeout=60)
    return response.json()
```

**Lines:** ~350

---

### 3. backend/open_webui/migrations/versions/XXX_add_agents_table.py

**Purpose:** Alembic migration for agent table

**Schema:**

```python
def upgrade():
    op.create_table(
        'agent',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('capabilities', sa.JSON(), nullable=True),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('input_schema', sa.JSON(), nullable=True),
        sa.Column('output_schema', sa.JSON(), nullable=True),
        sa.Column('default_input_modes', sa.JSON(), nullable=True),
        sa.Column('default_output_modes', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_agent_user_id', 'agent', ['user_id'])
    op.create_index('idx_agent_is_active', 'agent', ['is_active'])

def downgrade():
    op.drop_index('idx_agent_is_active', 'agent')
    op.drop_index('idx_agent_user_id', 'agent')
    op.drop_table('agent')
```

**Lines:** ~60

---

### 4. src/lib/components/admin/Settings/Connections/AgentConnection.svelte

**Purpose:** Admin UI for A2A agent management

**Key Features:**

```svelte
<script lang="ts">
  import { getA2AAgentsConfig, setA2AAgentsConfig, verifyA2AAgent } from '$lib/apis/configs'
  
  let enableA2AAgents = false
  let agentConnections = []
  let isVerifying = false
  
  async function loadConfig() {
    const config = await getA2AAgentsConfig($user.token)
    enableA2AAgents = config.ENABLE_A2A_AGENTS
    agentConnections = config.A2A_AGENT_CONNECTIONS || []
  }
  
  async function saveConfig() {
    await setA2AAgentsConfig($user.token, {
      ENABLE_A2A_AGENTS: enableA2AAgents,
      A2A_AGENT_CONNECTIONS: agentConnections
    })
    await loadConfig()
  }
  
  async function verifyConnection(connection) {
    isVerifying = true
    try {
      await verifyA2AAgent($user.token, connection)
      toast.success('Connection verified')
    } catch (e) {
      toast.error('Failed to verify connection')
    }
    isVerifying = false
  }
</script>

<!-- UI components: toggle, agent list, add/edit/delete buttons -->
```

**Lines:** ~400

---

### 5. test_a2a_integration.py

**Purpose:** End-to-end integration test

**Test Flow:**

```python
def test_a2a_integration(agent_url, openwebui_url, api_key, agent_name):
    # 1. Test Open WebUI connection
    response = requests.get(f"{openwebui_url}/api/health")
    assert response.status_code == 200
    
    # 2. Test agent discovery
    response = requests.get(f"{agent_url}/.well-known/agent.json")
    agent_info = response.json()
    
    # 3. Configure A2A agents
    config = {
        "ENABLE_A2A_AGENTS": True,
        "A2A_AGENT_CONNECTIONS": [{
            "url": agent_url,
            "name": agent_name,
            "config": {}
        }]
    }
    response = requests.post(
        f"{openwebui_url}/api/v1/configs/a2a_agents",
        json=config,
        headers={"Authorization": f"Bearer {api_key}"}
    )
    
    # 4. Wait for models refresh
    time.sleep(2)
    
    # 5. Get models list
    response = requests.get(
        f"{openwebui_url}/api/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    models = response.json()["data"]
    agent_models = [m for m in models if m.get("owned_by") == "a2a-agent"]
    
    # 6. Smart agent selection by URL
    agent_model = next(
        (m for m in agent_models if agent_url in m.get("info", {}).get("params", {}).get("url", "")),
        agent_models[0]
    )
    
    # 7. Test chat completion
    chat_request = {
        "model": agent_model["id"],
        "messages": [{"role": "user", "content": "Hello"}]
    }
    response = requests.post(
        f"{openwebui_url}/api/chat/completions",
        json=chat_request,
        headers={"Authorization": f"Bearer {api_key}"}
    )
    
    # 8. Validate response
    assert response.status_code == 200
    print("Test passed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-url", required=True)
    parser.add_argument("--openwebui-url", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--agent-name", default="Test Agent")
    args = parser.parse_args()
    
    test_a2a_integration(args.agent_url, args.openwebui_url, args.api_key, args.agent_name)
```

**Lines:** ~180

---

## Modified Files

### 1. backend/open_webui/main.py

**Changes:**

```python
# Line ~50: Import agent router
from open_webui.routers.agents import router as agents_router

# Line ~150: Register agent router
app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"])

# Lines 1145-1150: Reactive cache refresh in chat completion
@app.post("/api/chat/completions")
async def generate_chat_completions(form_data: GenerateChatCompletionForm, user=Depends(get_verified_user)):
    log.info(f"[CHAT] Request for model: {form_data.model}")
    
    available_models = request.app.state.MODELS.get("data", [])
    log.info(f"[CHAT] Available models in cache: {len(available_models)}")
    
    # Reactive cache refresh if model not found
    if not any(m["id"] == form_data.model for m in available_models):
        log.info(f"[CHAT] Model {form_data.model} not in cache, refreshing...")
        await get_all_models(request, user=user)
        available_models = request.app.state.MODELS.get("data", [])
        log.info(f"[CHAT] After refresh, available models: {len(available_models)}")
    
    # Route to A2A agent if model ID starts with a2a-agent-
    if form_data.model.startswith("a2a-agent-"):
        log.info(f"[CHAT] Routing to A2A agent: {form_data.model}")
        return await generate_a2a_agent_chat_completion(form_data, user)
    
    # ... existing chat completion logic
```

**Lines Modified:** ~10 additions

---

### 2. backend/open_webui/routers/configs.py

**Changes:**

```python
# Lines ~50-70: New Pydantic models
class AgentConnection(BaseModel):
    url: str
    name: str
    config: dict = {}

class AgentConnectionsConfigForm(BaseModel):
    ENABLE_A2A_AGENTS: bool = False
    A2A_AGENT_CONNECTIONS: List[AgentConnection] = []

# Lines ~400-450: New endpoints
@router.get("/a2a_agents")
async def get_a2a_agents_config(request: Request, user=Depends(get_admin_user)):
    """Get A2A agents configuration"""
    config = {
        "ENABLE_A2A_AGENTS": app.state.config.ENABLE_A2A_AGENTS,
        "A2A_AGENT_CONNECTIONS": app.state.config.A2A_AGENT_CONNECTIONS
    }
    return config

@router.post("/a2a_agents")
async def set_a2a_agents_config(
    request: Request,
    form_data: AgentConnectionsConfigForm,
    user=Depends(get_admin_user)
):
    """Set A2A agents configuration and sync to database"""
    log.info(f"[CONFIG] Setting A2A config: {form_data.model_dump()}")
    
    app.state.config.ENABLE_A2A_AGENTS = form_data.ENABLE_A2A_AGENTS
    app.state.config.A2A_AGENT_CONNECTIONS = [c.model_dump() for c in form_data.A2A_AGENT_CONNECTIONS]
    
    # Sync to database
    for connection in form_data.A2A_AGENT_CONNECTIONS:
        try:
            # Fetch agent discovery
            agent_url = connection.url
            if not agent_url.startswith("http"):
                agent_url = f"http://{agent_url}"
            
            response = requests.get(f"{agent_url}/.well-known/agent.json", timeout=10)
            agent_info = response.json()
            
            # Register in database
            agent_form = AgentForm(
                name=connection.name or agent_info.get("name", "Unknown"),
                endpoint=agent_info.get("endpoint", "/"),
                url=agent_url,
                version=agent_info.get("version"),
                description=agent_info.get("description"),
                capabilities=agent_info.get("capabilities", [])
            )
            Agents.insert_new_agent(agent_form, user.id)
            log.info(f"[CONFIG] Registered agent: {agent_form.name}")
            
        except Exception as e:
            log.error(f"[CONFIG] Failed to register agent {connection.url}: {e}")
    
    # Proactive cache refresh
    await get_all_models(request, user=user)
    log.info(f"[CONFIG] Models cache refreshed")
    
    return app.state.config.model_dump()

@router.post("/a2a_agents/verify")
async def verify_a2a_agent_connection(
    connection: AgentConnection,
    user=Depends(get_admin_user)
):
    """Verify A2A agent connection by fetching discovery document"""
    try:
        agent_url = connection.url
        if not agent_url.startswith("http"):
            agent_url = f"http://{agent_url}"
        
        response = requests.get(f"{agent_url}/.well-known/agent.json", timeout=10)
        response.raise_for_status()
        agent_info = response.json()
        
        return {
            "success": True,
            "agent_info": agent_info
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to verify connection: {str(e)}")
```

**Lines Modified:** ~150 additions

---

### 3. backend/open_webui/utils/models.py

**Critical Bug Fix:**

```python
# Lines 67-68: REMOVED (early return bug)
# BEFORE:
if len(models) == 0:
    return []

# AFTER:
# (removed - allow function to continue and add A2A agents)
```

**A2A Agent Aggregation:**

```python
# Lines 229-268: NEW
async def get_all_models(request: Request, user=None):
    log.info("[MODELS] Starting model aggregation")
    
    # ... existing model fetching logic for OpenAI/Ollama
    
    # Fetch A2A agents from database
    try:
        agents = Agents.get_agents()
        log.info(f"[MODELS] Fetched {len(agents)} A2A agents from database")
        
        for agent in agents:
            if not agent.is_active:
                continue
            
            model_id = f"a2a-agent-{agent.id}"
            model = {
                "id": model_id,
                "name": agent.name,
                "object": "model",
                "created": int(agent.created_at.timestamp()) if agent.created_at else 0,
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
            log.info(f"[MODELS] Added A2A agent model: {model_id}")
    
    except Exception as e:
        log.error(f"[MODELS] Failed to fetch A2A agents: {e}")
    
    # Cache models
    request.app.state.MODELS = {"data": models}
    log.info(f"[MODELS] Cached {len(models)} total models")
    
    return models
```

**Lines Modified:** 2 removed, ~40 added

---

### 4. backend/open_webui/utils/chat.py

**New Function:**

```python
# Lines ~800-900: NEW
async def generate_a2a_agent_chat_completion(
    form_data: GenerateChatCompletionForm,
    user: UserModel
) -> StreamingResponse:
    """Generate chat completion using A2A agent"""
    
    # Extract agent ID from model name
    agent_id = form_data.model.replace("a2a-agent-", "")
    log.info(f"[A2A] Looking up agent: {agent_id}")
    
    # Get agent from database
    agent = Agents.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get last message
    last_message = form_data.messages[-1]
    
    # Format JSON-RPC request
    json_rpc_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "messageId": str(uuid.uuid4()),
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": last_message.role,
                "parts": [
                    {
                        "text": last_message.content
                    }
                ]
            }
        },
        "id": 1
    }
    
    log.info(f"[A2A] Sending message to {agent.url}")
    
    # Send request to agent
    try:
        response = requests.post(
            agent.url,
            json=json_rpc_request,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        log.info(f"[A2A] Received response from agent")
        
    except requests.exceptions.RequestException as e:
        log.error(f"[A2A] Failed to send message to agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent communication failed: {str(e)}")
    
    # Parse response with fallback chain
    content = None
    
    # Try: result.artifacts[0].parts[0].text
    if "result" in data and "artifacts" in data["result"]:
        artifacts = data["result"]["artifacts"]
        if artifacts and len(artifacts) > 0:
            parts = artifacts[0].get("parts", [])
            if parts and len(parts) > 0:
                content = parts[0].get("text")
    
    # Fallback: result.message.parts[0].text
    if not content and "result" in data and "message" in data["result"]:
        message = data["result"]["message"]
        parts = message.get("parts", [])
        if parts and len(parts) > 0:
            content = parts[0].get("text")
    
    # Fallback: result.text or result as string
    if not content and "result" in data:
        result = data["result"]
        content = result.get("text", str(result))
    
    # Final fallback
    if not content:
        content = "Agent returned empty response"
        log.warning(f"[A2A] Could not parse response: {data}")
    
    log.info(f"[A2A] Parsed content length: {len(content)}")
    
    # Stream response in OpenAI format
    def generate():
        chunk = {
            "id": str(uuid.uuid4()),
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": form_data.model,
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": None
                }
            ]
        }
        yield f"data: {json.dumps(chunk)}\n\n"
        
        # Send done
        chunk["choices"][0]["delta"] = {}
        chunk["choices"][0]["finish_reason"] = "stop"
        yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

**Lines Modified:** ~100 additions

---

### 5. src/lib/components/admin/Settings/Connections.svelte

**Changes:**

```svelte
<script lang="ts">
  import AgentConnection from './Connections/AgentConnection.svelte'
  // ... existing imports
</script>

<!-- Existing connection sections -->

<!-- NEW: A2A Agents section -->
<div class="mb-8">
  <div class="mb-4">
    <h3 class="text-lg font-semibold">A2A Agents</h3>
    <p class="text-sm text-gray-500">
      Configure A2A (Agent-to-Agent) protocol connections
    </p>
  </div>
  
  <AgentConnection />
</div>
```

**Lines Modified:** ~15 additions

---

### 6. src/lib/apis/configs/index.ts

**Changes:**

```typescript
// NEW: A2A agent API functions

export const getA2AAgentsConfig = async (token: string = '') => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/configs/a2a_agents`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` })
    }
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail ?? err;
      console.log(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const setA2AAgentsConfig = async (token: string = '', config: object) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/configs/a2a_agents`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` })
    },
    body: JSON.stringify(config)
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail ?? err;
      console.log(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};

export const verifyA2AAgent = async (token: string = '', connection: object) => {
  let error = null;

  const res = await fetch(`${WEBUI_API_BASE_URL}/configs/a2a_agents/verify`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` })
    },
    body: JSON.stringify(connection)
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      return res.json();
    })
    .catch((err) => {
      error = err.detail ?? err;
      console.log(err);
      return null;
    });

  if (error) {
    throw error;
  }

  return res;
};
```

**Lines Modified:** ~90 additions

---

## Summary Statistics

**New Files:** 5
- Total new lines: ~1,240

**Modified Files:** 6
- Total lines added: ~305
- Total lines removed: 2

**Total Code Impact:**
- Lines added: ~1,545
- Lines removed: 2
- Net change: +1,543 lines

**File Breakdown:**
1. agents.py: ~250 lines (new)
2. agents router: ~350 lines (new)
3. migration: ~60 lines (new)
4. AgentConnection.svelte: ~400 lines (new)
5. test_a2a_integration.py: ~180 lines (new)
6. main.py: +10 lines (modified)
7. configs.py: +150 lines (modified)
8. models.py: -2, +40 lines (modified)
9. chat.py: +100 lines (modified)
10. Connections.svelte: +15 lines (modified)
11. configs/index.ts: +90 lines (modified)

**Impact Analysis:**

**Critical Changes:**
- models.py early return removal (2 lines) - Enabled entire A2A functionality

**Core Functionality:**
- Database layer: ~250 lines
- API layer: ~500 lines
- Chat integration: ~100 lines
- Cache management: ~50 lines

**UI/Frontend:**
- Admin settings: ~415 lines
- API client: ~90 lines

**Testing:**
- Integration test: ~180 lines

**Documentation:**
- Three markdown files: ~2,000 lines total
