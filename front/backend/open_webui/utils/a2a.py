"""Helpers for A2A discovery and JSON-RPC calls."""

from __future__ import annotations

from typing import Any, Optional
from urllib.parse import urlparse

import requests


def normalize_agent_base_url(agent_url: str) -> str:
    """Normalize an agent URL to a scheme and host base URL."""
    url = agent_url.strip()
    if not url.startswith(("http://", "https://")):
        if "localhost" in url or "127.0.0.1" in url:
            url = f"http://{url}"
        else:
            url = f"https://{url}"

    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def well_known_url_for_agent(agent_url: str, deployment_mode: Optional[str] = None) -> str:
    """Return the discovery-card URL for an agent."""
    if deployment_mode == "internal":
        return f"{agent_url.rstrip('/')}/.well-known/agent.json"
    return f"{normalize_agent_base_url(agent_url)}/.well-known/agent.json"


def cloud_run_audience(endpoint: str) -> str:
    """Return the Cloud Run service audience for an endpoint URL."""
    parsed_url = urlparse(endpoint)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def authenticated_cloud_run_headers(endpoint: str) -> dict[str, str]:
    """Build identity-token auth headers for a private Cloud Run service."""
    from google.auth.transport.requests import Request as GoogleAuthRequest
    from google.oauth2 import id_token

    token = id_token.fetch_id_token(
        GoogleAuthRequest(), cloud_run_audience(endpoint)
    )
    return {"Authorization": f"Bearer {token}"}


def a2a_request_headers(
    endpoint: str, cloud_run_auth_required: bool = False
) -> dict[str, str]:
    """Return HTTP headers for an A2A request."""
    headers = {"Content-Type": "application/json"}
    if cloud_run_auth_required:
        headers.update(authenticated_cloud_run_headers(endpoint))
    return headers


def fetch_agent_card(
    agent_url: str,
    *,
    deployment_mode: Optional[str] = None,
    cloud_run_auth_required: bool = False,
    timeout: int = 10,
) -> dict[str, Any]:
    """Fetch an A2A discovery card without invoking the agent model."""
    well_known_url = well_known_url_for_agent(agent_url, deployment_mode)
    response = requests.get(
        well_known_url,
        headers=a2a_request_headers(well_known_url, cloud_run_auth_required),
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def post_jsonrpc_to_agent(
    endpoint: str,
    payload: dict[str, Any],
    *,
    cloud_run_auth_required: bool = False,
    timeout: int = 60,
) -> requests.Response:
    """Post a JSON-RPC payload to an A2A endpoint."""
    normalized_endpoint = endpoint.rstrip("/")
    return requests.post(
        normalized_endpoint,
        json=payload,
        headers=a2a_request_headers(
            normalized_endpoint, cloud_run_auth_required
        ),
        timeout=timeout,
    )
