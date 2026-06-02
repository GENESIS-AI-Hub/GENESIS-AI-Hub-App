"""Unit tests for agent trust tier enforcement.

Tests the _get_user_scope, _enforce_tier, and one-time-use elevated token
helpers in routers/agents.py — pure logic tests with no database or network.
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
from open_webui.routers.agents import (
    _get_user_scope,
    _enforce_tier,
    _elevated_token_hash,
    _is_elevated_token_consumed,
    _consume_elevated_token,
    _reset_used_elevated_tokens,
)


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


class TestOsuRoleJwtPayloadSeam:
    """Priority 5 seam: _enforce_tier reads osu_role from jwt_payload when
    the JWT carries the claim (post-#141 OSU OIDC), falling back to
    user.osu_role for backward compat."""

    def test_jwt_payload_osu_role_grants_access(self):
        """Staff agent allows user when jwt_payload carries osu_role=staff."""
        agent = _make_agent("authenticated", required_role="staff")
        user = SimpleNamespace(id="u1", role="user")  # no osu_role attr
        _enforce_tier(agent, user, jwt_payload={"osu_role": "staff"})

    def test_jwt_payload_osu_role_blocks_wrong_role(self):
        """Staff agent blocks user when jwt_payload carries osu_role=student."""
        agent = _make_agent("authenticated", required_role="staff")
        user = SimpleNamespace(id="u1", role="user")
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(agent, user, jwt_payload={"osu_role": "student"})
        assert exc_info.value.detail["code"] == "role_required"

    def test_jwt_payload_takes_precedence_over_user_attr(self):
        """JWT osu_role overrides user.osu_role when both are present."""
        agent = _make_agent("authenticated", required_role="staff")
        user = SimpleNamespace(id="u1", role="user", osu_role="student")
        _enforce_tier(agent, user, jwt_payload={"osu_role": "staff"})

    def test_no_jwt_payload_falls_back_to_user_attr(self):
        """Without jwt_payload, falls back to user.osu_role (existing behaviour)."""
        agent = _make_agent("authenticated", required_role="staff")
        user = SimpleNamespace(id="u1", role="user", osu_role="staff")
        _enforce_tier(agent, user, jwt_payload=None)

    def test_empty_jwt_payload_falls_back_to_user_attr(self):
        """Empty jwt_payload dict falls back to user.osu_role."""
        agent = _make_agent("authenticated", required_role="student")
        user = SimpleNamespace(id="u1", role="user", osu_role="student")
        _enforce_tier(agent, user, jwt_payload={})


class TestOneTimeUseElevatedToken:
    """Priority 7: elevated tokens are consumed on first privileged-agent call.

    §6.5 of the architecture doc requires one-time-use to prevent replay attacks.
    NOTE: _used_elevated_tokens is in-memory / per-process — not Redis. This is
    documented as dev-only; production hardening is tracked in #142.
    """

    def setup_method(self):
        _reset_used_elevated_tokens()

    def _future(self) -> float:
        import time
        return time.time() + 1800

    def test_first_privileged_call_with_elevated_token_succeeds(self):
        """Initial call to a privileged agent with a valid elevated token passes."""
        _enforce_tier(
            _make_agent("privileged"),
            _make_user("user"),
            elevated_until=self._future(),
            raw_token="tok-abc",
        )

    def test_second_privileged_call_with_same_token_is_blocked(self):
        """After the token is consumed on the first call, a second call is denied."""
        token = "tok-replay"
        elevated_until = self._future()
        _enforce_tier(
            _make_agent("privileged"),
            _make_user("user"),
            elevated_until=elevated_until,
            raw_token=token,
        )
        with pytest.raises(HTTPException) as exc_info:
            _enforce_tier(
                _make_agent("privileged"),
                _make_user("user"),
                elevated_until=elevated_until,
                raw_token=token,
            )
        assert exc_info.value.detail["code"] == "step_up_required"

    def test_admin_privileged_access_does_not_consume_token(self):
        """Admin is permanently privileged; the elevated token is not consumed."""
        token = "tok-admin"
        elevated_until = self._future()
        _enforce_tier(
            _make_agent("privileged"),
            _make_user("admin"),
            elevated_until=elevated_until,
            raw_token=token,
        )
        # Second call with same token should still succeed (token was not consumed)
        _enforce_tier(
            _make_agent("privileged"),
            _make_user("admin"),
            elevated_until=elevated_until,
            raw_token=token,
        )

    def test_token_not_consumed_for_non_privileged_agents(self):
        """Elevated token is only consumed when the agent requires privileged tier."""
        token = "tok-auth-agent"
        elevated_until = self._future()
        # Call to authenticated-tier agent — should NOT consume the token
        _enforce_tier(
            _make_agent("authenticated"),
            _make_user("user"),
            elevated_until=elevated_until,
            raw_token=token,
        )
        # Same token can still be used for a privileged agent afterward
        _enforce_tier(
            _make_agent("privileged"),
            _make_user("user"),
            elevated_until=elevated_until,
            raw_token=token,
        )

    def test_different_tokens_are_independent(self):
        """Two different elevated tokens are tracked independently."""
        elevated_until = self._future()
        _enforce_tier(
            _make_agent("privileged"),
            _make_user("user"),
            elevated_until=elevated_until,
            raw_token="tok-first",
        )
        # A different token should still work even though tok-first is consumed
        _enforce_tier(
            _make_agent("privileged"),
            _make_user("user"),
            elevated_until=elevated_until,
            raw_token="tok-second",
        )

    def test_token_without_raw_token_does_not_block_but_still_grants(self):
        """If raw_token is not passed, one-time-use check is skipped (backwards compat)."""
        elevated_until = self._future()
        # Both calls should pass — no raw_token means no consumption tracking
        _enforce_tier(
            _make_agent("privileged"),
            _make_user("user"),
            elevated_until=elevated_until,
            raw_token=None,
        )
        _enforce_tier(
            _make_agent("privileged"),
            _make_user("user"),
            elevated_until=elevated_until,
            raw_token=None,
        )

    def test_consumed_token_hash_helper(self):
        """Direct unit test of the consume/check helpers."""
        token_hash = _elevated_token_hash("my-secret-token")
        assert not _is_elevated_token_consumed(token_hash)
        _consume_elevated_token(token_hash, self._future())
        assert _is_elevated_token_consumed(token_hash)

    def test_expired_token_hash_is_pruned(self):
        """Entries with elapsed elevated_until are cleaned up on the next check."""
        import time
        token_hash = _elevated_token_hash("tok-expired")
        _consume_elevated_token(token_hash, time.time() - 1)  # already expired
        # After pruning the entry is gone → token appears "unconsumed"
        assert not _is_elevated_token_consumed(token_hash)
