"""Unit tests for agent trust tier enforcement.

Tests the _get_user_scope and _enforce_tier helpers in routers/agents.py
without requiring a database or network — pure logic tests.
"""

import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock
from fastapi import HTTPException


def _make_user(role: str):
    return SimpleNamespace(id="u1", role=role)


def _make_agent(trust_tier: str, required_role: str | None = None):
    return SimpleNamespace(trust_tier=trust_tier, required_role=required_role)


# Import after defining helpers so import errors surface cleanly
from open_webui.routers.agents import _get_user_scope, _enforce_tier


class TestGetUserScope:
    def test_admin_maps_to_privileged(self):
        assert _get_user_scope(_make_user("admin")) == "privileged"

    def test_user_maps_to_authenticated(self):
        assert _get_user_scope(_make_user("user")) == "authenticated"

    def test_pending_maps_to_public(self):
        assert _get_user_scope(_make_user("pending")) == "public"

    def test_unknown_role_maps_to_public(self):
        assert _get_user_scope(_make_user("something_else")) == "public"


class TestEnforceTier:
    # --- access granted cases ---

    def test_public_agent_allows_pending_user(self):
        _enforce_tier(_make_agent("public"), _make_user("pending"))  # no exception

    def test_public_agent_allows_authenticated_user(self):
        _enforce_tier(_make_agent("public"), _make_user("user"))

    def test_public_agent_allows_admin(self):
        _enforce_tier(_make_agent("public"), _make_user("admin"))

    def test_authenticated_agent_allows_user(self):
        _enforce_tier(_make_agent("authenticated"), _make_user("user"))

    def test_authenticated_agent_allows_admin(self):
        _enforce_tier(_make_agent("authenticated"), _make_user("admin"))

    def test_privileged_agent_allows_admin(self):
        _enforce_tier(_make_agent("privileged"), _make_user("admin"))

    # --- access denied cases ---

    def test_authenticated_agent_blocks_pending_user(self):
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(_make_agent("authenticated"), _make_user("pending"))
        error = exc_info.value
        assert error.status_code == 403
        assert error.detail["code"] == "tier_required"
        assert error.detail["required_tier"] == "authenticated"

    def test_privileged_agent_blocks_pending_user(self):
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(_make_agent("privileged"), _make_user("pending"))
        error = exc_info.value
        assert error.status_code == 403
        assert error.detail["code"] == "tier_required"

    def test_privileged_agent_blocks_authenticated_user_with_step_up(self):
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(_make_agent("privileged"), _make_user("user"))
        error = exc_info.value
        assert error.status_code == 403
        assert error.detail["code"] == "step_up_required"
        assert error.detail["required_tier"] == "privileged"

    def test_structured_403_includes_required_role(self):
        agent = _make_agent("authenticated", required_role="staff")
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(agent, _make_user("pending"))
        assert exc_info.value.detail["required_role"] == "staff"

    def test_unknown_tier_defaults_to_public_access(self):
        # Agents with unrecognised tier values fall back to 0 (public)
        _enforce_tier(_make_agent("unknown_tier"), _make_user("pending"))


class TestGetUserScopeNoneUser:
    """None user represents unauthenticated callers on optional-auth endpoints
    like internal-a2a that public-tier agents must still serve."""

    def test_none_user_maps_to_public(self):
        assert _get_user_scope(None) == "public"

    def test_none_user_passes_public_tier_agent(self):
        _enforce_tier(_make_agent("public"), None)

    def test_none_user_blocked_by_authenticated_tier(self):
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(_make_agent("authenticated"), None)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "tier_required"

    def test_none_user_blocked_by_privileged_tier(self):
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(_make_agent("privileged"), None)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "tier_required"


class TestElevatedUntilScope:
    """elevated_until grants a temporary privileged window for authenticated users.

    This covers the step-up MFA path: after /step-up/callback, the JWT carries
    an elevated_until claim and _get_user_scope upgrades the scope to 'privileged'
    until the timestamp expires.
    """

    def _future(self) -> float:
        import time
        return time.time() + 1800  # 30 min from now

    def _past(self) -> float:
        import time
        return time.time() - 1  # already expired

    def test_active_elevation_promotes_user_to_privileged(self):
        assert _get_user_scope(_make_user("user"), elevated_until=self._future()) == "privileged"

    def test_expired_elevation_falls_back_to_base_scope(self):
        assert _get_user_scope(_make_user("user"), elevated_until=self._past()) == "authenticated"

    def test_elevation_not_needed_for_admin(self):
        # Admin is always privileged regardless of elevated_until
        assert _get_user_scope(_make_user("admin"), elevated_until=None) == "privileged"

    def test_active_elevation_allows_privileged_agent(self):
        # Authenticated user with active step-up can reach privileged agents
        _enforce_tier(_make_agent("privileged"), _make_user("user"), elevated_until=self._future())

    def test_expired_elevation_blocks_privileged_agent(self):
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(_make_agent("privileged"), _make_user("user"), elevated_until=self._past())
        assert exc_info.value.detail["code"] == "step_up_required"


class TestRequiredRoleMatrix:
    """After OSU OIDC (#141) lands, _get_user_scope should read user.osu_role
    (staff, student, faculty, …) and _enforce_tier should check it against
    agent.required_role.  The tests below pin the expected behaviour."""

    def test_staff_agent_allows_staff_user(self):
        agent = _make_agent("authenticated", required_role="staff")
        user = SimpleNamespace(id="u1", role="user", osu_role="staff")
        _enforce_tier(agent, user)

    def test_staff_agent_blocks_student_user(self):
        agent = _make_agent("authenticated", required_role="staff")
        user = SimpleNamespace(id="u1", role="user", osu_role="student")
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(agent, user)
        assert exc_info.value.detail["required_role"] == "staff"

    def test_student_agent_allows_student_user(self):
        agent = _make_agent("authenticated", required_role="student")
        user = SimpleNamespace(id="u1", role="user", osu_role="student")
        _enforce_tier(agent, user)

    def test_student_agent_blocks_no_role_user(self):
        agent = _make_agent("authenticated", required_role="student")
        user = SimpleNamespace(id="u1", role="user", osu_role=None)
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(agent, user)
        assert exc_info.value.detail["required_role"] == "student"
