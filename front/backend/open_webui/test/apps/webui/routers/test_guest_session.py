"""Unit tests for the guest session flow (§3 guest / headless session handling).

Tests cover:
  - GuestUser attributes and role mapping
  - get_guest_or_verified_user dependency behaviour for guest vs regular JWTs
  - Trust tier enforcement for GuestUser (public allowed, authenticated blocked)
  - _get_user_scope correctly maps GuestUser.role="pending" to "public"

These are pure logic tests — no database or HTTP server required.
The conftest.py in this directory stubs all heavy dependencies.
"""

import time
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from fastapi import HTTPException


# ── Import helpers under test ─────────────────────────────────────────────────

from open_webui.utils.auth import GuestUser
from open_webui.routers.agents import _get_user_scope, _enforce_tier, _reset_used_elevated_tokens


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_agent(trust_tier: str, required_role: str | None = None):
    return SimpleNamespace(trust_tier=trust_tier, required_role=required_role)


# ── GuestUser ─────────────────────────────────────────────────────────────────

class TestGuestUser:
    def test_role_is_pending(self):
        """GuestUser.role='pending' maps to 'public' scope via _get_user_scope."""
        assert GuestUser().role == "pending"

    def test_session_type_is_guest(self):
        assert GuestUser().session_type == "guest"

    def test_osu_role_is_public(self):
        assert GuestUser().osu_role == "public"

    def test_id_is_empty_string(self):
        assert GuestUser().id == ""

    def test_scope_maps_to_public(self):
        """_get_user_scope treats GuestUser (pending role) as public tier."""
        assert _get_user_scope(GuestUser()) == "public"


# ── Tier enforcement for guest users ─────────────────────────────────────────

class TestGuestTierEnforcement:
    def setup_method(self):
        _reset_used_elevated_tokens()

    def test_guest_can_access_public_agents(self):
        """Guest passes tier check for public-tier agents."""
        _enforce_tier(_make_agent("public"), GuestUser())

    def test_guest_blocked_from_authenticated_agents(self):
        """Guest is blocked from authenticated-tier agents with tier_required code."""
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(_make_agent("authenticated"), GuestUser())
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "tier_required"
        assert exc_info.value.detail["required_tier"] == "authenticated"

    def test_guest_blocked_from_privileged_agents(self):
        """Guest is blocked from privileged-tier agents."""
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(_make_agent("privileged"), GuestUser())
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "tier_required"
        assert exc_info.value.detail["required_tier"] == "privileged"

    def test_guest_blocked_structured_403_matches_frontend_expectation(self):
        """The 403 detail dict has both code and required_tier keys.

        ChrisChat.svelte catches this and shows the inline login prompt when
        code == 'tier_required'. Both keys must be present.
        """
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(_make_agent("authenticated"), GuestUser())
        detail = exc_info.value.detail
        assert "code" in detail
        assert "required_tier" in detail

    def test_guest_osu_role_is_not_checked_for_public_agents(self):
        """required_role is only enforced on agents with authenticated+ tier.
        A public-tier agent with required_role is a misconfiguration; the role
        check is skipped and the guest passes the public-tier access check."""
        # public tier + required_role → role check skipped → guest allowed
        _enforce_tier(_make_agent("public", required_role="staff"), GuestUser())

    def test_guest_blocked_before_osu_role_check_on_authenticated_agent(self):
        """Tier failure is raised first — osu_role check is never reached for guests."""
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(_make_agent("authenticated", required_role="staff"), GuestUser())
        assert exc_info.value.detail["code"] == "tier_required"


# ── GuestUser in _get_user_scope and _enforce_tier  ──────────────────────────
# Note: get_guest_or_verified_user is a FastAPI dependency that requires a
# running app + real auth module.  Its JWT-routing logic (guest token →
# GuestUser, regular token → DB lookup) is tested through the integration test
# suite (Cypress/Playwright) which requires the full dev stack.
# The unit tests above verify the downstream behaviour: once GuestUser is
# returned, the tier system correctly scopes it to public-only access.
