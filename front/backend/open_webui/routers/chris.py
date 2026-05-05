"""
Chris orchestrator agent router.

Exposes:
  POST /api/v1/chris/message   — route a user message to an installed agent or answer directly.
  GET  /api/v1/chris/suggestions — return marketplace agents relevant to a query.

Chris uses Gemini to classify the user's intent and select the best installed
agent.  If no agent matches (or none are installed) Chris answers directly.
"""

import logging
import uuid
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from open_webui.constants import ERROR_MESSAGES
from open_webui.models.agents import AgentModel, Agents
from open_webui.models.registry import RegistryAgents
from open_webui.utils.auth import get_verified_user
from open_webui.utils.chris_gemini import chat as gemini_chat

log = logging.getLogger(__name__)

router = APIRouter()

############################
# Pydantic models
############################

CHRIS_SYSTEM_PROMPT = (
    "You are Chris, the OpenBeavs AI hub orchestrator. "
    "You help users by routing their queries to the right specialized agent, "
    "or by answering directly when no agent fits."
)

# Used only for the direct-fallback path so Gemini never invents agent names in prose.
_CHRIS_DIRECT_SYSTEM_PROMPT_BASE = (
    "You are Chris, the OpenBeavs AI hub assistant. "
    "You are answering the user directly — there is no agent being called right now. "
    "NEVER invent or guess agent names. Only refer to agents that appear in the "
    "INSTALLED AGENTS list below. If the list is empty, say the user has no agents installed."
)


def _build_direct_system_prompt(agents: list[AgentModel]) -> str:
    """Build the direct-answer system prompt, injecting the real installed-agent list."""
    if agents:
        agent_lines = "\n".join(
            f"- {a.name}" + (f": {a.description}" if a.description else "")
            for a in agents
        )
        agent_section = f"\n\nINSTALLED AGENTS:\n{agent_lines}"
    else:
        agent_section = "\n\nINSTALLED AGENTS: none"
    return _CHRIS_DIRECT_SYSTEM_PROMPT_BASE + agent_section


class HistoryMessage(BaseModel):
    """A single turn in the conversation history."""

    role: str
    content: str


class ChrisMessageForm(BaseModel):
    """Request body for POST /api/v1/chris/message."""

    message: str
    chat_id: Optional[str] = None
    history: list[HistoryMessage] = []


class ChrisMessageResponse(BaseModel):
    """Response from the Chris message endpoint."""

    routed_to: Optional[str] = None  # agent id, or None if answered directly
    agent_name: Optional[str] = None
    response: str


class SuggestionItem(BaseModel):
    """A single marketplace agent suggestion."""

    id: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    url: str


############################
# Helpers
############################


def _build_routing_prompt(user_message: str, agents: list[AgentModel]) -> str:
    """Build the Gemini prompt used to decide which agent should handle the query.

    The prompt is intentionally conservative: Gemini should prefer 'none' unless
    the agent's skills/description strongly and specifically match the user's query.
    """
    agent_lines = "\n".join(
        f"- id={a.id!r}: name={a.name!r}, description={a.description or 'none'!r}, "
        f"skills={a.skills or []}"
        for a in agents
    )
    valid_ids = ", ".join(repr(a.id) for a in agents)
    return (
        f"You are a strict router. The ONLY valid output values are listed below.\n\n"
        f"VALID IDs (you may ONLY reply with one of these, or the word none):\n{valid_ids}\n\n"
        f"Agents:\n{agent_lines}\n\n"
        f'User message: "{user_message}"\n\n'
        "Task: decide whether one of the above agents is the RIGHT tool for this exact message.\n"
        "Rules:\n"
        "1. Only choose an agent if its skills or description SPECIFICALLY and CLEARLY match "
        "the user's intent — not just a vague overlap.\n"
        "2. ALWAYS reply with none for: greetings, small talk, how-are-you, thanks, jokes, "
        "general questions, anything Chris can answer directly, or any message where you are "
        "not certain an agent is the right fit.\n"
        "3. Reply with ONLY one of the exact id strings listed in VALID IDs above, or the word: none\n"
        "4. Do NOT invent or guess any id. If the right id is not in the VALID IDs list, reply: none\n"
        "5. No explanation, no punctuation, no quotes — just the id or the word none.\n"
        "Your answer:"
    )


def _extract_text_from_a2a_response(response_data: dict) -> str:
    """Pull the first text part out of an A2A JSON-RPC result.

    Handles two known A2A result shapes:
      1. ``result.artifacts[0].parts[0].text`` (standard A2A)
      2. ``result.parts[0].text`` (simplified agent responses)

    Returns an empty string when the result is absent, empty, or contains no text.
    """
    result = response_data.get("result", {})
    if not result:
        return ""
    # A2A result shape: { artifacts: [ { parts: [ { text: "..." } ] } ] }
    artifacts = result.get("artifacts")
    if artifacts is not None:
        if artifacts and artifacts[0].get("parts"):
            return artifacts[0]["parts"][0].get("text", "")
        return ""
    # Fallback: some agents use result.parts directly
    parts = result.get("parts")
    if parts is not None:
        return parts[0].get("text", "") if parts else ""
    return ""


def _call_agent_a2a(agent: AgentModel, message: str) -> str:
    """Send a message to an agent via A2A JSON-RPC and return the text reply."""
    endpoint = agent.endpoint or agent.url
    if not endpoint:
        raise ValueError(f"Agent {agent.id} has no endpoint configured.")

    message_id = str(uuid.uuid4())
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": message_id,
                "role": "user",
                "parts": [{"text": message, "type": "text"}],
            }
        },
        "id": 1,
    }

    response = requests.post(endpoint, json=jsonrpc_request, timeout=30)
    response.raise_for_status()
    return _extract_text_from_a2a_response(response.json())


def _score_registry_agent(query_words: set[str], agent) -> int:
    """Keyword overlap score between query words and agent metadata."""
    searchable = " ".join(
        filter(
            None,
            [
                agent.name or "",
                agent.description or "",
                str(agent.tools or ""),
            ],
        )
    ).lower()
    return sum(1 for w in query_words if w in searchable)


############################
# POST /message
############################


@router.post("/message", response_model=ChrisMessageResponse)
async def chris_message(
    form_data: ChrisMessageForm,
    user=Depends(get_verified_user),
) -> ChrisMessageResponse:
    """Route a user message to the best installed agent, or answer directly via Gemini.

    1. Fetch the user's installed agents.
    2. If agents exist, ask Gemini which one should handle the query.
    3. Call the selected agent via A2A JSON-RPC.
    4. On failure or if no agent fits, fall back to a direct Gemini answer.
    """
    user_message = form_data.message.strip()
    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    installed_agents = Agents.get_agents()
    # Exclude the Chris system agent itself from routing candidates
    installed_agents = [a for a in installed_agents if a.id != "chris"]

    history_messages = [{"role": m.role, "content": m.content} for m in form_data.history]

    # ── Step 1: routing decision ──────────────────────────────────────────────
    selected_agent: Optional[AgentModel] = None

    if installed_agents:
        routing_prompt = _build_routing_prompt(user_message, installed_agents)
        valid_agent_ids = {a.id for a in installed_agents}
        try:
            routing_messages = [
                {"role": "system", "content": CHRIS_SYSTEM_PROMPT},
                {"role": "user", "content": routing_prompt},
            ]
            raw_decision = await gemini_chat(routing_messages)
            chosen_id = raw_decision.strip().strip('"').strip("'").lower()
            log.info(f"Chris routing decision: {chosen_id!r} (raw: {raw_decision!r})")

            # Hard-validate: only accept IDs that actually exist in the installed set.
            # Any hallucinated or off-list response is treated as "none".
            if chosen_id != "none":
                if chosen_id not in valid_agent_ids:
                    log.warning(
                        f"Chris returned {chosen_id!r} which is not a valid installed agent id "
                        f"(valid: {valid_agent_ids}). Treating as none."
                    )
                    chosen_id = "none"
                else:
                    selected_agent = next(
                        (a for a in installed_agents if a.id == chosen_id), None
                    )
        except Exception as e:
            log.warning(f"Chris routing decision failed, falling back to direct: {e}")

    # ── Step 2a: delegate to selected agent ───────────────────────────────────
    if selected_agent:
        try:
            agent_reply = _call_agent_a2a(selected_agent, user_message)
            return ChrisMessageResponse(
                routed_to=selected_agent.id,
                agent_name=selected_agent.name,
                response=agent_reply,
            )
        except Exception as e:
            log.warning(
                f"Agent {selected_agent.id} unreachable ({e}), falling back to Chris."
            )

    # ── Step 2b: answer directly via Gemini ───────────────────────────────────
    direct_messages = [
        {"role": "system", "content": _build_direct_system_prompt(installed_agents)},
        *history_messages,
        {"role": "user", "content": user_message},
    ]
    try:
        direct_reply = await gemini_chat(direct_messages)
    except Exception as e:
        log.error(f"Chris direct Gemini call failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chris is temporarily unavailable. Please try again shortly.",
        )

    return ChrisMessageResponse(routed_to=None, agent_name=None, response=direct_reply)


############################
# GET /suggestions
############################


@router.get("/suggestions", response_model=list[SuggestionItem])
async def chris_suggestions(
    q: str = "",
    limit: int = 3,
    user=Depends(get_verified_user),
) -> list[SuggestionItem]:
    """Return marketplace registry agents relevant to a query that the user hasn't installed yet.

    Args:
        q: The user's query string for relevance scoring.
        limit: Maximum number of suggestions to return (default 3).
    """
    # IDs of agents already installed by this user
    installed_ids = {a.id for a in Agents.get_agents()}
    # Also match by URL to catch agents registered via URL
    installed_urls = {a.url for a in Agents.get_agents() if a.url}

    registry_agents = RegistryAgents.get_agents_by_user_id(user.id, permission="read")

    candidates = [
        a
        for a in registry_agents
        if a.id not in installed_ids and a.url not in installed_urls
    ]

    if not q.strip():
        # No query — return most recently added
        candidates.sort(key=lambda a: a.created_at, reverse=True)
        return [
            SuggestionItem(
                id=a.id,
                name=a.name,
                description=a.description,
                image_url=a.image_url,
                url=a.url,
            )
            for a in candidates[:limit]
        ]

    query_words = set(q.lower().split())
    scored = sorted(candidates, key=lambda a: _score_registry_agent(query_words, a), reverse=True)

    return [
        SuggestionItem(
            id=a.id,
            name=a.name,
            description=a.description,
            image_url=a.image_url,
            url=a.url,
        )
        for a in scored[:limit]
    ]
