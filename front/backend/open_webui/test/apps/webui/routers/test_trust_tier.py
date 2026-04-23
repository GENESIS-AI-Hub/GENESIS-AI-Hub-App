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
