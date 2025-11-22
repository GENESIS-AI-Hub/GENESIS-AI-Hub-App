from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, ConfigDict

from typing import Optional

from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.config import get_config, save_config
from open_webui.config import BannerModel

from open_webui.utils.tools import get_tool_server_data, get_tool_servers_data


router = APIRouter()


############################
# ImportConfig
############################


class ImportConfigForm(BaseModel):
    config: dict


@router.post("/import", response_model=dict)
async def import_config(form_data: ImportConfigForm, user=Depends(get_admin_user)):
    save_config(form_data.config)
    return get_config()


############################
# ExportConfig
############################


@router.get("/export", response_model=dict)
async def export_config(user=Depends(get_admin_user)):
    return get_config()


############################
# Direct Connections Config
############################


class DirectConnectionsConfigForm(BaseModel):
    ENABLE_DIRECT_CONNECTIONS: bool


@router.get("/direct_connections", response_model=DirectConnectionsConfigForm)
async def get_direct_connections_config(request: Request, user=Depends(get_admin_user)):
    return {
        "ENABLE_DIRECT_CONNECTIONS": request.app.state.config.ENABLE_DIRECT_CONNECTIONS,
    }


@router.post("/direct_connections", response_model=DirectConnectionsConfigForm)
async def set_direct_connections_config(
    request: Request,
    form_data: DirectConnectionsConfigForm,
    user=Depends(get_admin_user),
):
    request.app.state.config.ENABLE_DIRECT_CONNECTIONS = (
        form_data.ENABLE_DIRECT_CONNECTIONS
    )
    return {
        "ENABLE_DIRECT_CONNECTIONS": request.app.state.config.ENABLE_DIRECT_CONNECTIONS,
    }


############################
# ToolServers Config
############################


class ToolServerConnection(BaseModel):
    url: str
    path: str
    auth_type: Optional[str]
    key: Optional[str]
    config: Optional[dict]

    model_config = ConfigDict(extra="allow")


class ToolServersConfigForm(BaseModel):
    TOOL_SERVER_CONNECTIONS: list[ToolServerConnection]


@router.get("/tool_servers", response_model=ToolServersConfigForm)
async def get_tool_servers_config(request: Request, user=Depends(get_admin_user)):
    return {
        "TOOL_SERVER_CONNECTIONS": request.app.state.config.TOOL_SERVER_CONNECTIONS,
    }


@router.post("/tool_servers", response_model=ToolServersConfigForm)
async def set_tool_servers_config(
    request: Request,
    form_data: ToolServersConfigForm,
    user=Depends(get_admin_user),
):
    request.app.state.config.TOOL_SERVER_CONNECTIONS = [
        connection.model_dump() for connection in form_data.TOOL_SERVER_CONNECTIONS
    ]

    request.app.state.TOOL_SERVERS = await get_tool_servers_data(
        request.app.state.config.TOOL_SERVER_CONNECTIONS
    )

    return {
        "TOOL_SERVER_CONNECTIONS": request.app.state.config.TOOL_SERVER_CONNECTIONS,
    }


@router.post("/tool_servers/verify")
async def verify_tool_servers_config(
    request: Request, form_data: ToolServerConnection, user=Depends(get_admin_user)
):
    """
    Verify the connection to the tool server.
    """
    try:

        token = None
        if form_data.auth_type == "bearer":
            token = form_data.key
        elif form_data.auth_type == "session":
            token = request.state.token.credentials

        url = f"{form_data.url}/{form_data.path}"
        return await get_tool_server_data(token, url)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to the tool server: {str(e)}",
        )


############################
# CodeInterpreterConfig
############################
class CodeInterpreterConfigForm(BaseModel):
    ENABLE_CODE_EXECUTION: bool
    CODE_EXECUTION_ENGINE: str
    CODE_EXECUTION_JUPYTER_URL: Optional[str]
    CODE_EXECUTION_JUPYTER_AUTH: Optional[str]
    CODE_EXECUTION_JUPYTER_AUTH_TOKEN: Optional[str]
    CODE_EXECUTION_JUPYTER_AUTH_PASSWORD: Optional[str]
    CODE_EXECUTION_JUPYTER_TIMEOUT: Optional[int]
    ENABLE_CODE_INTERPRETER: bool
    CODE_INTERPRETER_ENGINE: str
    CODE_INTERPRETER_PROMPT_TEMPLATE: Optional[str]
    CODE_INTERPRETER_JUPYTER_URL: Optional[str]
    CODE_INTERPRETER_JUPYTER_AUTH: Optional[str]
    CODE_INTERPRETER_JUPYTER_AUTH_TOKEN: Optional[str]
    CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD: Optional[str]
    CODE_INTERPRETER_JUPYTER_TIMEOUT: Optional[int]


@router.get("/code_execution", response_model=CodeInterpreterConfigForm)
async def get_code_execution_config(request: Request, user=Depends(get_admin_user)):
    return {
        "ENABLE_CODE_EXECUTION": request.app.state.config.ENABLE_CODE_EXECUTION,
        "CODE_EXECUTION_ENGINE": request.app.state.config.CODE_EXECUTION_ENGINE,
        "CODE_EXECUTION_JUPYTER_URL": request.app.state.config.CODE_EXECUTION_JUPYTER_URL,
        "CODE_EXECUTION_JUPYTER_AUTH": request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH,
        "CODE_EXECUTION_JUPYTER_AUTH_TOKEN": request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN,
        "CODE_EXECUTION_JUPYTER_AUTH_PASSWORD": request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD,
        "CODE_EXECUTION_JUPYTER_TIMEOUT": request.app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT,
        "ENABLE_CODE_INTERPRETER": request.app.state.config.ENABLE_CODE_INTERPRETER,
        "CODE_INTERPRETER_ENGINE": request.app.state.config.CODE_INTERPRETER_ENGINE,
        "CODE_INTERPRETER_PROMPT_TEMPLATE": request.app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE,
        "CODE_INTERPRETER_JUPYTER_URL": request.app.state.config.CODE_INTERPRETER_JUPYTER_URL,
        "CODE_INTERPRETER_JUPYTER_AUTH": request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH,
        "CODE_INTERPRETER_JUPYTER_AUTH_TOKEN": request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN,
        "CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD": request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD,
        "CODE_INTERPRETER_JUPYTER_TIMEOUT": request.app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT,
    }


@router.post("/code_execution", response_model=CodeInterpreterConfigForm)
async def set_code_execution_config(
    request: Request, form_data: CodeInterpreterConfigForm, user=Depends(get_admin_user)
):

    request.app.state.config.ENABLE_CODE_EXECUTION = form_data.ENABLE_CODE_EXECUTION

    request.app.state.config.CODE_EXECUTION_ENGINE = form_data.CODE_EXECUTION_ENGINE
    request.app.state.config.CODE_EXECUTION_JUPYTER_URL = (
        form_data.CODE_EXECUTION_JUPYTER_URL
    )
    request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH = (
        form_data.CODE_EXECUTION_JUPYTER_AUTH
    )
    request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN = (
        form_data.CODE_EXECUTION_JUPYTER_AUTH_TOKEN
    )
    request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD = (
        form_data.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD
    )
    request.app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT = (
        form_data.CODE_EXECUTION_JUPYTER_TIMEOUT
    )

    request.app.state.config.ENABLE_CODE_INTERPRETER = form_data.ENABLE_CODE_INTERPRETER
    request.app.state.config.CODE_INTERPRETER_ENGINE = form_data.CODE_INTERPRETER_ENGINE
    request.app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE = (
        form_data.CODE_INTERPRETER_PROMPT_TEMPLATE
    )

    request.app.state.config.CODE_INTERPRETER_JUPYTER_URL = (
        form_data.CODE_INTERPRETER_JUPYTER_URL
    )

    request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH = (
        form_data.CODE_INTERPRETER_JUPYTER_AUTH
    )

    request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN = (
        form_data.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN
    )
    request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD = (
        form_data.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD
    )
    request.app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT = (
        form_data.CODE_INTERPRETER_JUPYTER_TIMEOUT
    )

    return {
        "ENABLE_CODE_EXECUTION": request.app.state.config.ENABLE_CODE_EXECUTION,
        "CODE_EXECUTION_ENGINE": request.app.state.config.CODE_EXECUTION_ENGINE,
        "CODE_EXECUTION_JUPYTER_URL": request.app.state.config.CODE_EXECUTION_JUPYTER_URL,
        "CODE_EXECUTION_JUPYTER_AUTH": request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH,
        "CODE_EXECUTION_JUPYTER_AUTH_TOKEN": request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_TOKEN,
        "CODE_EXECUTION_JUPYTER_AUTH_PASSWORD": request.app.state.config.CODE_EXECUTION_JUPYTER_AUTH_PASSWORD,
        "CODE_EXECUTION_JUPYTER_TIMEOUT": request.app.state.config.CODE_EXECUTION_JUPYTER_TIMEOUT,
        "ENABLE_CODE_INTERPRETER": request.app.state.config.ENABLE_CODE_INTERPRETER,
        "CODE_INTERPRETER_ENGINE": request.app.state.config.CODE_INTERPRETER_ENGINE,
        "CODE_INTERPRETER_PROMPT_TEMPLATE": request.app.state.config.CODE_INTERPRETER_PROMPT_TEMPLATE,
        "CODE_INTERPRETER_JUPYTER_URL": request.app.state.config.CODE_INTERPRETER_JUPYTER_URL,
        "CODE_INTERPRETER_JUPYTER_AUTH": request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH,
        "CODE_INTERPRETER_JUPYTER_AUTH_TOKEN": request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_TOKEN,
        "CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD": request.app.state.config.CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD,
        "CODE_INTERPRETER_JUPYTER_TIMEOUT": request.app.state.config.CODE_INTERPRETER_JUPYTER_TIMEOUT,
    }


############################
# SetDefaultModels
############################
class ModelsConfigForm(BaseModel):
    DEFAULT_MODELS: Optional[str]
    MODEL_ORDER_LIST: Optional[list[str]]


@router.get("/models", response_model=ModelsConfigForm)
async def get_models_config(request: Request, user=Depends(get_admin_user)):
    return {
        "DEFAULT_MODELS": request.app.state.config.DEFAULT_MODELS,
        "MODEL_ORDER_LIST": request.app.state.config.MODEL_ORDER_LIST,
    }


@router.post("/models", response_model=ModelsConfigForm)
async def set_models_config(
    request: Request, form_data: ModelsConfigForm, user=Depends(get_admin_user)
):
    request.app.state.config.DEFAULT_MODELS = form_data.DEFAULT_MODELS
    request.app.state.config.MODEL_ORDER_LIST = form_data.MODEL_ORDER_LIST
    return {
        "DEFAULT_MODELS": request.app.state.config.DEFAULT_MODELS,
        "MODEL_ORDER_LIST": request.app.state.config.MODEL_ORDER_LIST,
    }


class PromptSuggestion(BaseModel):
    title: list[str]
    content: str


class SetDefaultSuggestionsForm(BaseModel):
    suggestions: list[PromptSuggestion]


@router.post("/suggestions", response_model=list[PromptSuggestion])
async def set_default_suggestions(
    request: Request,
    form_data: SetDefaultSuggestionsForm,
    user=Depends(get_admin_user),
):
    data = form_data.model_dump()
    request.app.state.config.DEFAULT_PROMPT_SUGGESTIONS = data["suggestions"]
    return request.app.state.config.DEFAULT_PROMPT_SUGGESTIONS


############################
# SetBanners
############################


class SetBannersForm(BaseModel):
    banners: list[BannerModel]


@router.post("/banners", response_model=list[BannerModel])
async def set_banners(
    request: Request,
    form_data: SetBannersForm,
    user=Depends(get_admin_user),
):
    data = form_data.model_dump()
    request.app.state.config.BANNERS = data["banners"]
    return request.app.state.config.BANNERS


@router.get("/banners", response_model=list[BannerModel])
async def get_banners(
    request: Request,
    user=Depends(get_verified_user),
):
    return request.app.state.config.BANNERS


############################
# A2A Agent Connections Config
############################


class AgentConnection(BaseModel):
    url: str
    name: Optional[str] = None
    config: Optional[dict] = None

    model_config = ConfigDict(extra="allow")


class AgentConnectionsConfigForm(BaseModel):
    ENABLE_A2A_AGENTS: bool
    A2A_AGENT_CONNECTIONS: list[AgentConnection]


@router.get("/a2a_agents", response_model=AgentConnectionsConfigForm)
async def get_a2a_agents_config(request: Request, user=Depends(get_admin_user)):
    enable_a2a = getattr(request.app.state.config, "ENABLE_A2A_AGENTS", True)
    connections = getattr(request.app.state.config, "A2A_AGENT_CONNECTIONS", [])
    return {
        "ENABLE_A2A_AGENTS": enable_a2a,
        "A2A_AGENT_CONNECTIONS": connections,
    }


@router.post("/a2a_agents", response_model=AgentConnectionsConfigForm)
async def set_a2a_agents_config(
    request: Request,
    form_data: AgentConnectionsConfigForm,
    user=Depends(get_admin_user),
):
    from open_webui.models.agents import Agents
    import uuid as uuid_lib

    request.app.state.config.ENABLE_A2A_AGENTS = form_data.ENABLE_A2A_AGENTS
    request.app.state.config.A2A_AGENT_CONNECTIONS = [
        connection.model_dump() for connection in form_data.A2A_AGENT_CONNECTIONS
    ]

    # Sync connections to agents database
    if form_data.ENABLE_A2A_AGENTS:
        # Get existing agents
        existing_agents = {agent.endpoint or agent.url: agent for agent in Agents.get_agents()}
        print(f"Existing agents: {list(existing_agents.keys())}")

        for connection in form_data.A2A_AGENT_CONNECTIONS:
            agent_url = connection.url
            agent_name = connection.name or "A2A Agent"
            print(f"Processing agent: {agent_name} at {agent_url}")

            # Check if agent already exists by URL
            if agent_url not in existing_agents:
                print(f"Agent {agent_url} not in existing agents, registering...")
                # Fetch agent info from well-known endpoint
                try:
                    import requests as req
                    from urllib.parse import urlparse

                    url = agent_url.strip()
                    if not url.startswith(("http://", "https://")):
                        if "localhost" in url or "127.0.0.1" in url:
                            url = "http://" + url
                        else:
                            url = "https://" + url

                    parsed_url = urlparse(url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    well_known_url = f"{base_url}/.well-known/agent.json"

                    response = req.get(well_known_url, timeout=10)
                    agent_data = response.json() if response.ok else {}

                    # Register agent in database
                    agent_id = str(uuid_lib.uuid4())
                    Agents.insert_new_agent(
                        id=agent_id,
                        name=agent_name or agent_data.get("name", "A2A Agent"),
                        description=agent_data.get("description", ""),
                        endpoint=base_url,
                        url=base_url,
                        version=agent_data.get("version", "1.0.0"),
                        capabilities=agent_data.get("capabilities"),
                        skills=agent_data.get("skills"),
                        default_input_modes=agent_data.get("defaultInputModes"),
                        default_output_modes=agent_data.get("defaultOutputModes"),
                        user_id=user.id,
                    )
                except Exception as e:
                    # If fetching fails, still register with basic info
                    print(f"Error fetching agent info from {agent_url}: {e}")
                    import traceback
                    traceback.print_exc()
                    agent_id = str(uuid_lib.uuid4())
                    Agents.insert_new_agent(
                        id=agent_id,
                        name=agent_name,
                        description="A2A Agent Connection",
                        endpoint=agent_url,
                        url=agent_url,
                        user_id=user.id,
                    )

    # After syncing DB, refresh the in-memory models cache for this process
    # so newly-registered A2A agents are immediately available to the
    # chat/completions endpoint which checks request.app.state.MODELS.
    try:
        from open_webui.utils.models import get_all_models

        print(f"[CONFIG] Refreshing models cache after A2A agent registration...")
        await get_all_models(request, user=user)
        print(f"[CONFIG] Models cache refreshed. Cache now has {len(request.app.state.MODELS)} models")
    except Exception as e:
        print(f"[CONFIG] Failed to refresh models cache after A2A agent update: {e}")
        import traceback
        traceback.print_exc()

    return {
        "ENABLE_A2A_AGENTS": request.app.state.config.ENABLE_A2A_AGENTS,
        "A2A_AGENT_CONNECTIONS": request.app.state.config.A2A_AGENT_CONNECTIONS,
    }


@router.post("/a2a_agents/verify")
async def verify_a2a_agent_connection(
    request: Request, form_data: AgentConnection, user=Depends(get_admin_user)
):
    """
    Verify the connection to the A2A agent by fetching its .well-known/agent.json
    """
    import requests as req
    from urllib.parse import urlparse

    agent_url = form_data.url.strip()

    # Handle URLs without scheme
    if not agent_url.startswith(("http://", "https://")):
        # For localhost, default to http
        if "localhost" in agent_url or "127.0.0.1" in agent_url:
            agent_url = "http://" + agent_url
        else:
            agent_url = "https://" + agent_url

    # Parse the URL
    parsed_url = urlparse(agent_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    well_known_url = f"{base_url}/.well-known/agent.json"

    # Try to connect
    last_error = None
    for attempt_url in [well_known_url]:
        try:
            response = req.get(attempt_url, timeout=10)
            response.raise_for_status()
            agent_data = response.json()

            return {
                "success": True,
                "agent_info": agent_data,
                "url": base_url
            }
        except req.exceptions.SSLError as e:
            # If HTTPS fails on localhost, try HTTP
            if "localhost" in base_url or "127.0.0.1" in base_url:
                try:
                    http_url = base_url.replace("https://", "http://")
                    http_well_known = f"{http_url}/.well-known/agent.json"
                    response = req.get(http_well_known, timeout=10)
                    response.raise_for_status()
                    agent_data = response.json()

                    return {
                        "success": True,
                        "agent_info": agent_data,
                        "url": http_url
                    }
                except Exception as retry_error:
                    last_error = retry_error
            else:
                last_error = e
        except Exception as e:
            last_error = e

    # If all attempts failed, raise the last error
    error_detail = str(last_error) if last_error else "Unknown error"
    raise HTTPException(
        status_code=400,
        detail=f"Failed to connect to the A2A agent at {base_url}: {error_detail}",
    )
