"""Agent metadata refresh helpers."""

from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel

from open_webui.models.agents import AgentModel, Agents
from open_webui.utils.a2a import fetch_agent_card


log = logging.getLogger(__name__)


class AgentRefreshResult(BaseModel):
    """Result for a single agent metadata refresh."""

    id: str
    name: Optional[str] = None
    success: bool
    error: Optional[str] = None


def _metadata_from_card(card: dict[str, Any]) -> dict[str, Any]:
    metadata = {
        "name": card.get("name", "Unknown Agent"),
        "description": card.get("description", ""),
        "version": card.get("version", "1.0.0"),
        "capabilities": card.get("capabilities", {}),
        "skills": card.get("skills", []),
        "default_input_modes": card.get("defaultInputModes", ["text"]),
        "default_output_modes": card.get("defaultOutputModes", ["text"]),
    }

    profile_image_url = (
        card.get("profileImageUrl")
        or card.get("profile_image_url")
        or card.get("image_url")
    )
    if profile_image_url:
        metadata["profile_image_url"] = profile_image_url

    return metadata


def refresh_agent_metadata(agent: AgentModel) -> AgentRefreshResult:
    """Refresh one agent from its A2A discovery card."""
    if agent.deployment_mode == "internal" and agent.access_control is not None:
        return AgentRefreshResult(
            id=agent.id,
            name=agent.name,
            success=True,
        )

    agent_url = agent.endpoint or agent.url
    if not agent_url:
        return AgentRefreshResult(
            id=agent.id,
            name=agent.name,
            success=False,
            error="Agent has no endpoint or URL configured",
        )

    try:
        card = fetch_agent_card(
            agent_url,
            deployment_mode=agent.deployment_mode,
            cloud_run_auth_required=agent.cloud_run_auth_required,
        )
        updated_agent = Agents.update_agent_metadata_by_id(
            agent.id, _metadata_from_card(card)
        )
        if not updated_agent:
            return AgentRefreshResult(
                id=agent.id,
                name=agent.name,
                success=False,
                error="Failed to update agent metadata",
            )
        return AgentRefreshResult(
            id=updated_agent.id,
            name=updated_agent.name,
            success=True,
        )
    except Exception as exc:
        log.warning("Failed to refresh agent %s: %s", agent.id, exc)
        return AgentRefreshResult(
            id=agent.id,
            name=agent.name,
            success=False,
            error=str(exc),
        )


def refresh_all_agent_metadata() -> list[AgentRefreshResult]:
    """Refresh metadata for all active agents."""
    return [refresh_agent_metadata(agent) for agent in Agents.get_agents()]
