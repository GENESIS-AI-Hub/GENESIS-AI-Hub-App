"""
Gemini wrapper for the Chris orchestrator agent.

Uses Gemini's OpenAI-compatible REST endpoint so no extra SDK is needed
beyond the `openai` package already in requirements.
"""

import logging
from typing import Optional

import openai

from open_webui.config import GEMINI_API_KEY, CHRIS_MODEL

log = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


async def chat(messages: list[dict], model: Optional[str] = None) -> str:
    """Send a list of chat messages to Gemini and return the text reply.

    Args:
        messages: List of dicts with ``role`` and ``content`` keys.
        model: Gemini model ID to use. Defaults to the ``CHRIS_MODEL`` env var.

    Returns:
        The assistant's text response, or an empty string on failure.

    Raises:
        ValueError: If ``GEMINI_API_KEY`` is not configured.
    """
    api_key = GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured — Chris cannot respond.")

    target_model = model or CHRIS_MODEL

    try:
        client = openai.AsyncOpenAI(api_key=api_key, base_url=GEMINI_BASE_URL)
        response = await client.chat.completions.create(
            model=target_model,
            messages=messages,
        )
        return response.choices[0].message.content if response.choices else ""
    except Exception as e:
        log.error(f"Chris Gemini API error: {e}")
        raise
