from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import requests
import uuid
import json
import logging

from open_webui.models.agents import Agents
from open_webui.constants import ERROR_MESSAGES
from open_webui.utils.a2a import post_jsonrpc_to_agent
from starlette.responses import StreamingResponse

router = APIRouter()
log = logging.getLogger(__name__)

class EmbedAgentResponse(BaseModel):
    id: str
    name: str
    description: str
    profile_image_url: Optional[str] = None

@router.get("/agent/{agent_id}", response_model=EmbedAgentResponse)
async def get_agent_details(agent_id: str):
    agent = Agents.get_agent_by_id(agent_id)
    if not agent or agent.access_control is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return EmbedAgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        profile_image_url=agent.profile_image_url
    )

@router.get("/agents", response_model=List[EmbedAgentResponse])
async def get_available_agents():
    """List all available agents for selection in the embed view."""
    agents = Agents.get_agents()
    return [
        EmbedAgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            profile_image_url=agent.profile_image_url
        )
        for agent in agents
        if agent.is_active and agent.access_control is None
    ]

class EmbedChatRequest(BaseModel):
    model: str 
    messages: List[Dict[str, Any]]
    stream: bool = True

@router.post("/chat/completions")
async def embed_chat_completion(form_data: EmbedChatRequest):
    agent_id = form_data.model
    # If model ID starts with "agent:", strip it
    if agent_id.startswith("agent:"):
        agent_id = agent_id[6:]
    
    log.info(f"[EMBED] Chat request for agent: {agent_id}")
        
    agent = Agents.get_agent_by_id(agent_id)
    if not agent or agent.access_control is not None:
        log.error(f"[EMBED] Agent not found: {agent_id}")
        raise HTTPException(status_code=404, detail="Agent not found")
        
    if not agent.endpoint and not agent.url:
        log.error(f"[EMBED] Agent {agent_id} has no endpoint")
        raise HTTPException(status_code=400, detail="Agent has no endpoint configured. Please set an endpoint or URL for this agent.")
          
    endpoint = agent.endpoint or agent.url
    # Strip trailing slash
    endpoint = endpoint.rstrip('/')
    log.info(f"[EMBED] Using endpoint: {endpoint}")
    
    # Take the last user message
    last_message = next((m for m in reversed(form_data.messages) if m["role"] == "user"), None)
    if not last_message:
        log.error(f"[EMBED] No user message found in request")
        raise HTTPException(status_code=400, detail="No user message found")

    message_content = last_message.get("content", "")
    if isinstance(message_content, list):
        # Handle multimodal content - extract text
        text_parts = [p["text"] for p in message_content if p["type"] == "text"]
        message_content = " ".join(text_parts)
    
    log.info(f"[EMBED] User message: {message_content[:100]}...")

    # Build JSON-RPC request following A2A protocol
    # Based on utils/chat.py implementation (lines 97-110)
    message_id = str(uuid.uuid4())
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "messageId": message_id,  # Top-level messageId required by A2A spec
            "message": {
                "messageId": message_id,
                "role": "user",
                "parts": [{"text": message_content}],  # No "type" field per A2A spec
            }
        },
        "id": 1,
    }
    
    log.info(f"[EMBED] Sending A2A request to {endpoint}")
    log.debug(f"[EMBED] Request payload: {json.dumps(jsonrpc_request)}")

    try:
        response = post_jsonrpc_to_agent(
            endpoint,
            jsonrpc_request,
            cloud_run_auth_required=agent.cloud_run_auth_required,
            timeout=60,
        )
        log.info(f"[EMBED] Response status: {response.status_code}")
        
        if not response.ok:
            log.error(f"[EMBED] HTTP error {response.status_code}: {response.text[:200]}")
            response.raise_for_status()

        try:
            response_data = response.json()
            log.info(f"[EMBED] Response data keys: {list(response_data.keys())}")
        except Exception as json_error:
            log.error(f"[EMBED] Failed to parse JSON: {str(json_error)}, Response: {response.text[:200]}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agent returned invalid JSON: {str(json_error)}"
            )
        
        # Extract text from A2A response
        # Based on utils/chat.py implementation (lines 122-142)
        # A2A response format: result.artifacts[0].parts[0].text
        result = response_data.get("result", {})
        response_text = ""
        
        log.info(f"[EMBED] Result type: {type(result)}, keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        # Try new A2A format: result.artifacts[0].parts[0].text
        if isinstance(result, dict) and "artifacts" in result:
            artifacts = result.get("artifacts", [])
            log.info(f"[EMBED] Found artifacts: {len(artifacts)}")
            if artifacts and len(artifacts) > 0:
                artifact_parts = artifacts[0].get("parts", [])
                log.info(f"[EMBED] Artifact parts: {len(artifact_parts)}")
                if artifact_parts and len(artifact_parts) > 0:
                    response_text = artifact_parts[0].get("text", "")
                    log.info(f"[EMBED] Extracted from artifacts ({len(response_text)} chars)")

        # Fallback to old format if new format doesn't work
        if not response_text and isinstance(result, dict):
            parts = result.get("parts", [])
            log.info(f"[EMBED] Trying fallback format, parts: {len(parts) if isinstance(parts, list) else 'Not a list'}")
            if parts and isinstance(parts, list) and len(parts) > 0:
                response_text = parts[0].get("text", str(result))
                log.info(f"[EMBED] Extracted from parts ({len(response_text)} chars)")
            else:
                response_text = result.get("text", str(result))
                log.info(f"[EMBED] Extracted from text field ({len(response_text)} chars)")
        elif not response_text:
            response_text = str(result)
            log.warning(f"[EMBED] Using stringified result ({len(response_text)} chars)")
        
        if not response_text:
            log.error(f"[EMBED] Empty response text. Full response: {json.dumps(response_data)[:500]}")
            # Check if there's an error in the response
            if "error" in response_data:
                error_msg = response_data["error"].get("message", "Unknown error")
                log.error(f"[EMBED] Agent returned error: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Agent error: {error_msg}"
                )
            response_text = "I received your message but couldn't generate a response. Please check the agent configuration."

        log.info(f"[EMBED] Final response text: {response_text[:100]}...")

        # Create a generator for streaming response format (OpenAI compatible)
        async def generate():
            chunk_id = f"chatcmpl-{uuid.uuid4()}"
            created = int(uuid.uuid1().time // 10000000)
            
            # Send the content in a single chunk
            chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": form_data.model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": response_text},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            
            # Send done
            chunk["choices"][0]["delta"] = {}
            chunk["choices"][0]["finish_reason"] = "stop"
            yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except requests.exceptions.Timeout:
        log.error(f"[EMBED] Timeout communicating with agent endpoint: {endpoint}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Agent took too long to respond (timeout after 60s)"
        )
    except requests.exceptions.ConnectionError as e:
        log.error(f"[EMBED] Connection error to {endpoint}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Cannot connect to agent endpoint: {str(e)}"
        )
    except requests.exceptions.RequestException as e:
        log.error(f"[EMBED] Request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with agent: {str(e)}",
        )
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        log.error(f"[EMBED] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )
