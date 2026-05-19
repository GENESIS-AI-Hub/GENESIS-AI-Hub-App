import time
import uuid
import json
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
import requests


def _fetch_well_known(url: str, timeout: int = 10) -> requests.Response:
    """Fetch a URL, skipping TLS verification for localhost (mock CA in dev)."""
    host = urlparse(url).hostname or ""
    verify = host not in ("localhost", "127.0.0.1", "::1")
    return requests.get(url, timeout=timeout, verify=verify)

from open_webui.models.agents import (
    AgentModel,
    AgentResponse,
    RegisterAgentForm,
    RegisterAgentByUrlForm,
    AgentUpdateForm,
    DeployAgentForm,
    Agents,
)
from open_webui.models.registry import RegistryAgents
from open_webui.constants import ERROR_MESSAGES
from open_webui.utils.auth import (
    decode_token,
    get_admin_user,
    get_optional_user,
    get_verified_user,
)
from open_webui.utils.a2a_runtime import PROVIDER_DEFAULTS, run_agent_turn


def _get_elevated_until(request: Request) -> Optional[float]:
    """Extract the elevated_until timestamp from the request's JWT, if present."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        token = request.cookies.get("token", "")
    if not token:
        return None
    data = decode_token(token)
    return data.get("elevated_until") if data else None

router = APIRouter()

# Tier ordering: higher index = higher privilege
_TIER_ORDER = {"public": 0, "authenticated": 1, "privileged": 2}


def _get_user_scope(user, elevated_until: Optional[float] = None) -> str:
    """Map the existing Open WebUI role to a trust tier.

    TODO(#141/#143): Replace this with real OSU OIDC scope claims once the
    identity provider integration in #141 lands.  For now we use the platform
    role as a proxy:
      admin   → privileged
      user    → authenticated
      pending → public
      None    → public (unauthenticated callers on optional-auth endpoints)

    Step-up elevation: if the request's JWT carries a valid elevated_until
    timestamp (set by the step-up MFA callback), any authenticated user is
    temporarily treated as privileged for the duration.
    """
    if user is None:
        return "public"
    if elevated_until and time.time() < elevated_until:
        return "privileged"
    if user.role == "admin":
        return "privileged"
    if user.role == "user":
        return "authenticated"
    return "public"


def _enforce_tier(
    agent: AgentModel, user, elevated_until: Optional[float] = None
) -> None:
    """Raise a structured 403 if the user's scope is below the agent's tier."""
    required = _TIER_ORDER.get(agent.trust_tier or "public", 0)
    user_scope = _get_user_scope(user, elevated_until)
    available = _TIER_ORDER.get(user_scope, 0)

    if available < required:
        # Distinguish "you need to log in" from "you need step-up MFA"
        code = "tier_required" if user_scope == "public" else "step_up_required"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": code,
                "required_tier": agent.trust_tier,
                "required_role": agent.required_role,
            },
        )

    # Tier passed — check OSU role restriction if set (admin bypasses).
    # user.osu_role is populated after #141 (OSU OIDC) lands; until then
    # getattr returns None which correctly blocks role-restricted agents.
    if agent.required_role and user is not None and getattr(user, "role", None) != "admin":
        user_osu_role = getattr(user, "osu_role", None)
        if user_osu_role != agent.required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "role_required",
                    "required_tier": agent.trust_tier,
                    "required_role": agent.required_role,
                },
            )

############################
# JSON-RPC Message Models
############################


class JSONRPCMessage(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any]
    id: Optional[int] = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[int] = None


class A2AMessagePart(BaseModel):
    text: str
    type: str = "text"


class A2AMessage(BaseModel):
    messageId: str
    role: str
    parts: List[A2AMessagePart]


class SendMessageToAgentForm(BaseModel):
    message: str
    chat_id: Optional[str] = None


############################
# GetAgents
############################


@router.get("/", response_model=List[AgentResponse])
async def get_agents(user=Depends(get_verified_user)):
    """Get all active agents"""
    agents = Agents.get_agents()
    return [AgentResponse(**agent.model_dump()) for agent in agents]


@router.get("/all", response_model=List[AgentModel])
async def get_all_agents(user=Depends(get_admin_user)):
    """Get all agents including inactive (admin only)"""
    agents = Agents.get_all_agents()
    return agents


############################
# FetchWellKnown
############################


@router.get("/fetch-well-known")
async def fetch_agent_well_known(agent_url: str, user=Depends(get_verified_user)):
    """Fetch an agent's .well-known/agent.json file without registering"""
    if not agent_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent URL is required",
        )

    if not agent_url.startswith(("http://", "https://")):
        agent_url = "https://" + agent_url

    parsed_url = urlparse(agent_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    if "/.well-known/" in agent_url:
        well_known_url = agent_url
    else:
        well_known_url = f"{base_url}/.well-known/agent.json"

    try:
        response = requests.get(well_known_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching agent's .well-known/agent.json: {str(e)}",
        )


############################
# GetAgentsAsModels
############################


@router.get("/models")
async def get_agents_as_models(user=Depends(get_verified_user)):
    """Get all active agents formatted as models for the chat interface"""
    agents = Agents.get_agents()

    agent_models = []
    for agent in agents:
        model_id = f"agent:{agent.id}"
        agent_models.append({
            "id": model_id,
            "name": agent.name,
            "object": "model",
            "created": agent.created_at,
            "owned_by": "a2a-agent",
            "agent": {
                "id": agent.id,
                "description": agent.description,
                "endpoint": agent.endpoint or agent.url,
                "capabilities": agent.capabilities,
                "skills": agent.skills,
            },
            "info": {
                "meta": {
                    "description": agent.description,
                    "capabilities": agent.capabilities,
                }
            }
        })

    return {"data": agent_models}


############################
# GetAgentById
############################


@router.get("/{agent_id}", response_model=AgentModel)
async def get_agent_by_id(agent_id: str, user=Depends(get_verified_user)):
    """Get a specific agent by ID"""
    agent = Agents.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )
    return agent


############################
# RegisterAgent
############################

@router.post("/register", response_model=AgentModel)
async def register_agent(
    form_data: RegisterAgentForm,
    user=Depends(get_verified_user),
):
    """Register a new agent manually"""
    agent_id = str(uuid.uuid4())

    agent = Agents.insert_new_agent(
        id=agent_id,
        name=form_data.name,
        description=form_data.description,
        endpoint=form_data.endpoint,
        input_schema=form_data.input_schema,
        output_schema=form_data.output_schema,
        trust_tier=form_data.trust_tier,
        required_role=form_data.required_role,
        user_id=user.id,
    )

    if agent:
        return agent
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ERROR_MESSAGES.DEFAULT(),
    )


############################
# RegisterAgentByUrl
############################


@router.post("/register-by-url", response_model=AgentModel)
async def register_agent_by_url(
    form_data: RegisterAgentByUrlForm,
    user=Depends(get_verified_user),
):
    """Register a new agent by fetching its .well-known/agent.json file"""
    agent_url = form_data.agent_url

    if not agent_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent URL is required",
        )

    # Ensure the URL has proper scheme
    if not agent_url.startswith(("http://", "https://")):
        agent_url = "https://" + agent_url

    # If the URL already points to a well-known card, use it directly.
    # Otherwise construct the standard path from the base domain.
    parsed_url = urlparse(agent_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    if "/.well-known/" in agent_url:
        well_known_url = agent_url
    else:
        well_known_url = f"{base_url}/.well-known/agent.json"

    try:
        response = _fetch_well_known(well_known_url)
        response.raise_for_status()
        agent_data = response.json()

        # Extract information from well-known format
        name = agent_data.get("name", "Unknown Agent")
        description = agent_data.get("description", "")
        url = agent_data.get("url") or base_url
        version = agent_data.get("version", "1.0.0")
        capabilities = agent_data.get("capabilities", {})
        skills = agent_data.get("skills", [])
        default_input_modes = agent_data.get("defaultInputModes", ["text"])
        default_output_modes = agent_data.get("defaultOutputModes", ["text"])

        # Derive the A2A JSON-RPC endpoint from the well-known URL path.
        # ADK agents host their RPC handler at the path prefix before /.well-known/,
        # not at the base domain root (e.g. /a2a/trivia_agent/ not /).
        if "/.well-known/" in well_known_url:
            rpc_endpoint = well_known_url[: well_known_url.index("/.well-known/")] + "/"
        else:
            rpc_endpoint = base_url + "/"

        # Use provided profile image or default to favicon
        profile_image_url = form_data.profile_image_url or agent_data.get("profileImageUrl") or "/static/favicon.png"

        # Check if agent with this URL already exists
        existing_agent = Agents.get_agent_by_url(url)
        if existing_agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An agent with this URL is already registered",
            )

        # Generate a unique ID for the agent
        agent_id = str(uuid.uuid4())

        # Insert the agent into the database
        agent = Agents.insert_new_agent(
            id=agent_id,
            name=name,
            description=description,
            url=url,
            endpoint=rpc_endpoint,
            version=version,
            capabilities=capabilities,
            skills=skills,
            default_input_modes=default_input_modes,
            default_output_modes=default_output_modes,
            profile_image_url=profile_image_url,
            user_id=user.id,
        )
        
        if agent:
            return agent
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(),
        )
        
    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching agent's .well-known/agent.json file: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON response from agent: {str(e)}",
        )


############################
# FetchWellKnown
############################


@router.get("/fetch-well-known")
async def fetch_agent_well_known(agent_url: str, user=Depends(get_verified_user)):
    """Fetch an agent's .well-known/agent.json file without registering"""
    if not agent_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent URL is required",
        )

    # Ensure the URL has proper scheme
    if not agent_url.startswith(("http://", "https://")):
        agent_url = "https://" + agent_url

    # Parse the URL
    parsed_url = urlparse(agent_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    well_known_url = f"{base_url}/.well-known/agent.json"

    try:
        response = _fetch_well_known(well_known_url)
        response.raise_for_status()
        agent_data = response.json()
        return agent_data
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error fetching agent's .well-known/agent.json: {str(e)}",
        )


############################
# UpdateAgent
############################


@router.patch("/{agent_id}", response_model=AgentModel)
async def update_agent(
    agent_id: str,
    form_data: AgentUpdateForm,
    user=Depends(get_verified_user),
):
    """Update an agent"""
    agent = Agents.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    # Check if user has permission (owner or admin)
    if user.role != "admin" and agent.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    updated_agent = Agents.update_agent_by_id(agent_id, form_data)
    if updated_agent:
        return updated_agent
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ERROR_MESSAGES.DEFAULT(),
    )


############################
# DeleteAgent
############################


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, user=Depends(get_verified_user)):
    """Delete an agent"""
    agent = Agents.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    # Check if user has permission (owner or admin)
    if user.role != "admin" and agent.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    result = Agents.delete_agent_by_id(agent_id)
    if result:
        return {"success": True, "message": "Agent deleted successfully"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ERROR_MESSAGES.DEFAULT(),
    )


############################
# SendMessageToAgent
############################


@router.post("/{agent_id}/message")
async def send_message_to_agent(
    agent_id: str,
    form_data: SendMessageToAgentForm,
    request: Request,
    user=Depends(get_verified_user),
):
    """Send a message to an A2A agent using JSON-RPC protocol"""
    agent = Agents.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    _enforce_tier(agent, user, elevated_until=_get_elevated_until(request))

    if not agent.endpoint and not agent.url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent has no endpoint configured",
        )

    endpoint = agent.endpoint or agent.url

    # Build JSON-RPC request following A2A protocol
    message_id = str(uuid.uuid4())
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": message_id,
                "role": "user",
                "parts": [{"text": form_data.message, "type": "text"}],
            }
        },
        "id": 1,
    }

    try:
        # Send request to external agent (skip TLS check for localhost dev agents)
        _host = urlparse(endpoint).hostname or ""
        _verify = _host not in ("localhost", "127.0.0.1", "::1")
        response = requests.post(endpoint, json=jsonrpc_request, timeout=30, verify=_verify)
        response.raise_for_status()

        response_data = response.json()
        return {
            "success": True,
            "agent_response": response_data,
            "message_id": message_id,
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error communicating with agent: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing agent response: {str(e)}",
        )


############################
# GetAgentsAsModels
############################


@router.get("/models")
async def get_agents_as_models(user=Depends(get_verified_user)):
    """Get all active agents formatted as models for the chat interface"""
    agents = Agents.get_agents()

    models = []
    for agent in agents:
        model_id = f"agent:{agent.id}"
        models.append({
            "id": model_id,
            "name": agent.name,
            "object": "model",
            "created": agent.created_at,
            "owned_by": "a2a-agent",
            "agent": {
                "id": agent.id,
                "description": agent.description,
                "endpoint": agent.endpoint or agent.url,
                "capabilities": agent.capabilities,
                "skills": agent.skills,
            },
            "info": {
                "meta": {
                    "description": agent.description,
                    "capabilities": agent.capabilities,
                    "trust_tier": agent.trust_tier,
                    "required_role": agent.required_role,
                }
            }
        })

    return {"data": models}


############################
# Deploy Internal A2A Agent
############################


def _internal_agent_card(agent: AgentModel, endpoint: str) -> Dict[str, Any]:
    """Build an A2A /.well-known/agent.json card from an agent row."""
    return {
        "name": agent.name,
        "description": agent.description,
        "url": endpoint,
        "version": agent.version or "1.0.0",
        "capabilities": agent.capabilities or {"streaming": True},
        "defaultInputModes": agent.default_input_modes or ["text"],
        "defaultOutputModes": agent.default_output_modes or ["text"],
        "skills": agent.skills
        or [
            {
                "id": "chat",
                "name": agent.name,
                "description": agent.description,
                "tags": ["chat"],
                "examples": [],
            }
        ],
    }


@router.post("/deploy", response_model=AgentModel)
async def deploy_agent(
    request: Request,
    form_data: DeployAgentForm,
    user=Depends(get_admin_user),
):
    """Create a new internally-hosted A2A agent from a system prompt.

    The hub itself serves the agent at /api/v1/agents/{id}/internal-a2a.
    If `publish_to_registry` is true, the agent also appears in the public
    registry and therefore in the Agents workspace listing.
    """
    provider = (form_data.provider or "anthropic").lower()
    if provider not in PROVIDER_DEFAULTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider '{provider}'",
        )
    model = form_data.model or PROVIDER_DEFAULTS[provider]

    agent_id = str(uuid.uuid4())
    base_url = str(request.base_url).rstrip("/")
    internal_endpoint = f"{base_url}/api/v1/agents/{agent_id}/internal-a2a"

    deployment_mode = "internal"
    endpoint = internal_endpoint

    if form_data.deploy_to_cloud_run:
        from open_webui.utils import cloud_run as cloud_run_mod

        try:
            endpoint = cloud_run_mod.deploy_provider_agent(
                agent_id,
                provider=provider,
                model=model,
                system_prompt=form_data.system_prompt,
                profile_image_url=form_data.profile_image_url,
            )
            deployment_mode = "cloud_run"
        except cloud_run_mod.CloudRunDisabled as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            )
        except cloud_run_mod._cloud_run_deploy_error_cls() as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Cloud Run deploy failed: {exc}",
            )

    card_skills = [
        {
            "id": "chat",
            "name": form_data.name,
            "description": form_data.description,
            "tags": ["chat"],
            "examples": [],
        }
    ]

    agent = Agents.insert_new_agent(
        id=agent_id,
        name=form_data.name,
        description=form_data.description,
        endpoint=endpoint,
        url=endpoint,
        version="1.0.0",
        capabilities={"streaming": True},
        skills=card_skills,
        default_input_modes=["text"],
        default_output_modes=["text"],
        profile_image_url=form_data.profile_image_url,
        system_prompt=form_data.system_prompt,
        provider=provider,
        model=model,
        deployment_mode=deployment_mode,
        deployment_status="ready",
        trust_tier=form_data.trust_tier,
        required_role=form_data.required_role,
        user_id=user.id,
    )

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(),
        )

    if form_data.publish_to_registry:
        try:
            RegistryAgents.insert_new_agent(
                id=str(uuid.uuid4()),
                user_id=user.id,
                url=endpoint,
                name=form_data.name,
                description=form_data.description,
                image_url=form_data.profile_image_url,
                foundational_model=f"{provider}/{model}",
                tools={
                    "capabilities": {"streaming": True},
                    "skills": card_skills,
                },
                access_control=None,
                trust_tier=form_data.trust_tier,
                required_role=form_data.required_role,
            )
        except Exception as e:
            # Registry publish is best-effort; don't fail the deploy.
            import logging
            logging.getLogger(__name__).warning(
                f"Deploy succeeded but registry publish failed for agent {agent_id}: {e}"
            )

    return agent


@router.get("/{agent_id}/internal-a2a/.well-known/agent.json")
async def get_internal_agent_card(request: Request, agent_id: str):
    """A2A discovery card for an internally-hosted agent. Public by A2A spec."""
    agent = Agents.get_agent_by_id(agent_id)
    if not agent or agent.deployment_mode != "internal":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internal agent not found",
        )
    endpoint = agent.endpoint or (
        f"{str(request.base_url).rstrip('/')}/api/v1/agents/{agent_id}/internal-a2a"
    )
    return _internal_agent_card(agent, endpoint)


@router.post("/{agent_id}/internal-a2a")
async def internal_agent_jsonrpc(
    agent_id: str,
    request: Request,
    user=Depends(get_optional_user),
):
    """JSON-RPC handler for an internally-hosted agent.

    Authentication is optional: public-tier agents are accessible to
    unauthenticated callers (A2A federation). Authenticated/privileged agents
    require a valid bearer token with sufficient scope.
    """
    try:
        body = await request.json()
    except Exception:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"},
            "id": None,
        }

    req_id = body.get("id", 1)
    method = body.get("method")

    agent = Agents.get_agent_by_id(agent_id)
    if not agent or agent.deployment_mode != "internal":
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32004, "message": "Agent not found"},
            "id": req_id,
        }

    try:
        _enforce_tier(agent, user, elevated_until=_get_elevated_until(request))
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"message": exc.detail}
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32001, **detail},
            "id": req_id,
        }

    if method != "message/send":
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": f"Method '{method}' not supported",
            },
            "id": req_id,
        }

    params = body.get("params") or {}
    message = params.get("message") or {}
    parts = message.get("parts") or []
    user_text = ""
    if parts and isinstance(parts, list):
        user_text = parts[0].get("text", "") if isinstance(parts[0], dict) else ""

    try:
        reply = await run_agent_turn(
            provider=agent.provider or "anthropic",
            model=agent.model or PROVIDER_DEFAULTS.get(agent.provider or "anthropic"),
            system_prompt=agent.system_prompt or "",
            user_message=user_text,
        )
    except HTTPException as e:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32000, "message": str(e.detail)},
            "id": req_id,
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32000, "message": str(e)},
            "id": req_id,
        }

    return {
        "jsonrpc": "2.0",
        "result": {
            "artifacts": [
                {"parts": [{"text": reply, "type": "text"}]}
            ]
        },
        "id": req_id,
    }
