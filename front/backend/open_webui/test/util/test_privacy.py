"""Unit tests for open_webui.utils.privacy — source_domain extraction logic.

Priority 8 (§6 cross-domain isolation):  extract_source_domain reads the FAB
origin from (1) JWT payload, (2) Origin header, (3) Referer header.

These tests run without any database or network — only stdlib + FastAPI Request.
"""

import os
import sys

# Ensure the backend is on the Python path when tests are run from front/
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Stub open_webui.utils.auth so privacy.py's lazy import works without a real DB
import types
from unittest.mock import MagicMock, patch

_auth_stub = types.ModuleType("open_webui.utils.auth")
_auth_stub.decode_token = lambda token: None  # default: invalid / no claims
sys.modules.setdefault("open_webui.utils.auth", _auth_stub)

# Now we can safely import the real function under test
from open_webui.utils.privacy import extract_source_domain


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def _make_request(
    authorization: str = "",
    origin: str = "",
    referer: str = "",
    cookie_token: str = "",
) -> MagicMock:
    """Build a minimal mock Request with only the headers extract_source_domain reads."""
    headers: dict = {}
    if authorization:
        headers["Authorization"] = authorization
    if origin:
        headers["Origin"] = origin
    if referer:
        headers["Referer"] = referer

    cookies: dict = {}
    if cookie_token:
        cookies["token"] = cookie_token

    req = MagicMock()
    req.headers = headers
    req.cookies = cookies
    return req


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExtractSourceDomain:
    # --- Priority 1: JWT source_domain claim ---

    def test_jwt_source_domain_takes_priority(self):
        """JWT source_domain claim overrides Origin header."""
        with patch.object(
            sys.modules["open_webui.utils.auth"],
            "decode_token",
            return_value={"source_domain": "library.oregonstate.edu"},
        ):
            req = _make_request(
                authorization="Bearer fake-jwt",
                origin="https://registrar.oregonstate.edu",
            )
            assert extract_source_domain(req) == "library.oregonstate.edu"

    def test_jwt_without_source_domain_falls_through_to_origin(self):
        """JWT present but without source_domain → fall through to Origin."""
        with patch.object(
            sys.modules["open_webui.utils.auth"],
            "decode_token",
            return_value={"sub": "u1"},
        ):
            req = _make_request(
                authorization="Bearer fake-jwt",
                origin="https://library.oregonstate.edu",
            )
            assert extract_source_domain(req) == "library.oregonstate.edu"

    def test_invalid_jwt_returns_none_falls_through_to_origin(self):
        """decode_token returning None falls through to Origin."""
        with patch.object(
            sys.modules["open_webui.utils.auth"],
            "decode_token",
            return_value=None,
        ):
            req = _make_request(
                authorization="Bearer bad",
                origin="https://engineering.oregonstate.edu",
            )
            assert extract_source_domain(req) == "engineering.oregonstate.edu"

    def test_cookie_token_is_also_decoded(self):
        """Cookie token is read when Authorization header is absent."""
        with patch.object(
            sys.modules["open_webui.utils.auth"],
            "decode_token",
            return_value={"source_domain": "extension.oregonstate.edu"},
        ):
            req = _make_request(cookie_token="cookie-jwt")
            assert extract_source_domain(req) == "extension.oregonstate.edu"

    # --- Priority 2: HTTP Origin header ---

    def test_origin_header_extracted(self):
        """Origin header hostname is returned when JWT is absent."""
        req = _make_request(origin="https://library.oregonstate.edu")
        assert extract_source_domain(req) == "library.oregonstate.edu"

    def test_origin_strips_scheme_and_port(self):
        """Origin with non-standard port returns just the hostname."""
        req = _make_request(origin="https://dev.oregonstate.edu:3000")
        assert extract_source_domain(req) == "dev.oregonstate.edu"

    def test_origin_localhost(self):
        """Localhost origin (dev server) is handled correctly."""
        req = _make_request(origin="http://localhost:5173")
        assert extract_source_domain(req) == "localhost"

    # --- Priority 3: HTTP Referer header ---

    def test_referer_used_when_no_origin(self):
        """Referer hostname is the fallback when Origin is absent."""
        req = _make_request(referer="https://engineering.oregonstate.edu/some/path")
        assert extract_source_domain(req) == "engineering.oregonstate.edu"

    def test_referer_strips_path_and_query(self):
        """Referer with long URL returns just the hostname."""
        req = _make_request(
            referer="https://chemistry.oregonstate.edu/courses/ch231?q=exam#section"
        )
        assert extract_source_domain(req) == "chemistry.oregonstate.edu"

    # --- No domain determinable ---

    def test_no_headers_returns_none(self):
        """Returns None when no domain signal is present."""
        req = _make_request()
        assert extract_source_domain(req) is None
