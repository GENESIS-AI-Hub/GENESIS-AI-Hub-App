import uuid
import requests
from typing import Optional, List
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from open_webui.models.registry import (
    RegistryAgentModel,
    SubmitRegistryAgentForm,
    UpdateRegistryAgentForm,
    RegistryAgents,
)
from open_webui.constants import ERROR_MESSAGES
from open_webui.utils.auth import get_verified_user, get_admin_user

router = APIRouter()

############################
# Get Registry Agents
############################


@router.get("/", response_model=List[RegistryAgentModel])
async def get_registry_agents(user=Depends(get_verified_user)):
    """Get all registry agents visible to the user"""
    return RegistryAgents.get_agents_by_user_id(user.id, permission="read")


############################
# Submit Registry Agent
############################


@router.post("/", response_model=RegistryAgentModel)
async def submit_registry_agent(
    form_data: SubmitRegistryAgentForm,
    user=Depends(get_verified_user),
):
    """Submit a new agent to the registry by URL"""
    agent_url = form_data.url

    if not agent_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent URL is required",
        )

    # Ensure the URL has proper scheme
    if not agent_url.startswith(("http://", "https://")):
        agent_url = "https://" + agent_url

    # Parse the URL and normalize it to just the domain for the well-known file
    parsed_url = urlparse(agent_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    well_known_url = f"{base_url}/.well-known/agent.json"

    try:
        response = requests.get(well_known_url, timeout=10)
        response.raise_for_status()
        agent_data = response.json()

        # Extract information from well-known format
        name = agent_data.get("name", "Unknown Agent")
        description = agent_data.get("description", "")
        # Use the URL from the JSON if available, otherwise the base URL
        url = agent_data.get("url", base_url)
        
        # Use provided image_url or fallback to JSON
        image_url = form_data.image_url or agent_data.get("image_url")
        
        # Extract tools/capabilities summary
        tools = {
            "capabilities": agent_data.get("capabilities", {}),
            "skills": agent_data.get("skills", []),
        }

        # Generate new ID for the registry entry
        id = str(uuid.uuid4())

        # Create registry entry
        agent = RegistryAgents.insert_new_agent(
            id=id,
            user_id=user.id,
            url=url,
            name=name,
            description=description,
            image_url=image_url,
            foundational_model=form_data.foundational_model,
            tools=tools,
            access_control=form_data.access_control,
        )

        if agent:
            return agent
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(),
        )

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
# Update Registry Agent
############################


@router.put("/{id}", response_model=RegistryAgentModel)
async def update_registry_agent(
    id: str,
    form_data: UpdateRegistryAgentForm,
    user=Depends(get_verified_user),
):
    """Update a registry agent"""
    agent = RegistryAgents.get_agent_by_id(id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    # Check permissions (Owner or Admin)
    if user.role != "admin" and agent.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    updated_data = form_data.model_dump(exclude_unset=True)
    
    updated_agent = RegistryAgents.update_agent_by_id(id, updated_data)
    if updated_agent:
        return updated_agent
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ERROR_MESSAGES.DEFAULT(),
    )


############################
# Delete Registry Agent
############################


@router.delete("/{id}")
async def delete_registry_agent(
    id: str,
    user=Depends(get_verified_user),
):
    """Delete a registry agent"""
    agent = RegistryAgents.get_agent_by_id(id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    # Check permissions (Owner or Admin)
    if user.role != "admin" and agent.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    result = RegistryAgents.delete_agent_by_id(id)
    if result:
        return {"success": True}
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ERROR_MESSAGES.DEFAULT(),
    )
