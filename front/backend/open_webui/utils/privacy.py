"""Utilities for OpenBeavs chat-privacy architecture (§2, §6).

This module is intentionally lightweight (stdlib + utils.auth only) so it can
be imported in both routers and tests without pulling in heavy dependencies.
"""

import logging
from typing import Optional
from urllib.parse import urlparse

from fastapi import Request

log = logging.getLogger(__name__)


def extract_source_domain(request: Request) -> Optional[str]:
    """Derive the FAB origin domain for cross-domain isolation (§6).

    Priority:
      1. JWT payload's source_domain claim (set after #141 OSU OIDC lands)
      2. HTTP Origin header (most reliable for FAB cross-origin requests)
      3. HTTP Referer header hostname (fallback for same-origin or direct calls)

    Returns None when the domain cannot be determined.
    """
    # Lazy import to avoid circular dependencies — decode_token lives in utils.auth
    # which itself imports from utils.privacy in some configurations.
    from open_webui.utils.auth import decode_token  # noqa: PLC0415

    # 1. JWT claim — populated once OSU OIDC (#141) is wired in
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip() or request.cookies.get("token", "")
    if token:
        payload = decode_token(token)
        if payload and payload.get("source_domain"):
            return payload["source_domain"]

    # 2. Origin header (cross-origin FAB requests send this)
    origin = request.headers.get("Origin", "")
    if origin:
        parsed = urlparse(origin)
        if parsed.hostname:
            return parsed.hostname

    # 3. Referer hostname (same-origin or direct API calls)
    referer = request.headers.get("Referer", "")
    if referer:
        parsed = urlparse(referer)
        if parsed.hostname:
            return parsed.hostname

    return None
