"""
Unit tests for the Chris orchestrator router.

Covers:
  - Pure helper functions (_build_routing_prompt, _extract_text_from_a2a_response,
    _score_registry_agent)
  - POST /api/v1/chris/message  — routing, fallback, and error paths
  - GET  /api/v1/chris/suggestions — scoring, limit, and installed-agent filtering
"""

import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

# conftest.py has already stubbed out the open_webui import chain.
# Now we can safely import just what we need from the router.
from open_webui.routers.chris import (
    _build_routing_prompt,
    _extract_text_from_a2a_response,
    _score_registry_agent,
    router as chris_router,
)
from open_webui.utils.auth import get_verified_user
from open_webui.models.agents import AgentModel, _Agents
from open_webui.models.registry import _RegistryAgents


# ─── shared fixtures ──────────────────────────────────────────────────────────


def _make_user(id="user-1", role="user"):
    u = MagicMock()
    u.id = id
    u.role = role
    return u


def _make_agent(
    id="osu-agent",
    name="OSU Expert",
    description="Answers OSU questions",
    skills=None,
    endpoint="http://osu-agent/",
    url=None,
) -> AgentModel:
    return AgentModel(
        id=id,
        name=name,
        description=description,
        skills=skills or ["osu", "university"],
        endpoint=endpoint,
        url=url,
    )


def _make_registry_agent(id, name, description="", url="http://agent/", created_at=0):
    a = MagicMock()
    a.id = id
    a.name = name
    a.description = description
    a.tools = None
    a.url = url
    a.image_url = None
    a.created_at = created_at
    return a


def _make_app(user=None) -> FastAPI:
    """Minimal FastAPI app with only the Chris router and an injected user."""
    app = FastAPI()
    app.include_router(chris_router, prefix="/api/v1/chris")
    fake_user = user or _make_user()
    app.dependency_overrides[get_verified_user] = lambda: fake_user
    return app


@pytest.fixture(autouse=True)
def reset_db():
    """Wipe the in-memory agent stores before every test."""
    _Agents._reset()
    _RegistryAgents._reset()
    yield
    _Agents._reset()
    _RegistryAgents._reset()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Pure helper function tests (no FastAPI / no mocking needed)
# ─────────────────────────────────────────────────────────────────────────────


class TestBuildRoutingPrompt:
    def test_includes_user_message(self):
        agents = [_make_agent()]
        prompt = _build_routing_prompt("What is OSU tuition?", agents)
        assert "What is OSU tuition?" in prompt

    def test_includes_agent_id_and_name(self):
        agents = [_make_agent(id="osu-agent", name="OSU Expert")]
        prompt = _build_routing_prompt("hello", agents)
        assert "osu-agent" in prompt
        assert "OSU Expert" in prompt

    def test_includes_all_agents(self):
        agents = [
            _make_agent(id="agent-a", name="Agent A"),
            _make_agent(id="agent-b", name="Agent B"),
        ]
        prompt = _build_routing_prompt("query", agents)
        assert "agent-a" in prompt
        assert "agent-b" in prompt

    def test_instructs_none_as_valid_reply(self):
        prompt = _build_routing_prompt("hi", [_make_agent()])
        assert "none" in prompt.lower()

    def test_instructs_no_explanation(self):
        prompt = _build_routing_prompt("test", [_make_agent()])
        assert "No explanation" in prompt or "no explanation" in prompt.lower() or "just the id" in prompt.lower()


class TestExtractTextFromA2AResponse:
    def test_standard_artifacts_shape(self):
        data = {
            "result": {
                "artifacts": [
                    {"parts": [{"text": "Hello from agent", "type": "text"}]}
                ]
            }
        }
        assert _extract_text_from_a2a_response(data) == "Hello from agent"

    def test_fallback_result_parts_shape(self):
        data = {"result": {"parts": [{"text": "Direct part"}]}}
        assert _extract_text_from_a2a_response(data) == "Direct part"

    def test_empty_response_returns_empty_string(self):
        assert _extract_text_from_a2a_response({}) == ""

    def test_empty_result_returns_empty_string(self):
        assert _extract_text_from_a2a_response({"result": {}}) == ""

    def test_empty_artifacts_list_returns_empty_string(self):
        data = {"result": {"artifacts": []}}
        assert _extract_text_from_a2a_response(data) == ""

    def test_empty_parts_returns_empty_string(self):
        data = {"result": {"artifacts": [{"parts": []}]}}
        assert _extract_text_from_a2a_response(data) == ""

    def test_multiple_artifacts_returns_first(self):
        data = {
            "result": {
                "artifacts": [
                    {"parts": [{"text": "First", "type": "text"}]},
                    {"parts": [{"text": "Second", "type": "text"}]},
                ]
            }
        }
        assert _extract_text_from_a2a_response(data) == "First"


class TestScoreRegistryAgent:
    def _agent(self, name, description, tools=None):
        a = MagicMock()
        a.name = name
        a.description = description
        a.tools = tools
        return a

    def test_matching_words_add_to_score(self):
        agent = self._agent("OSU Expert", "Answers OSU university questions")
        score = _score_registry_agent({"osu", "university"}, agent)
        assert score == 2

    def test_no_overlap_returns_zero(self):
        agent = self._agent("Weather Bot", "weather forecasts and rain")
        score = _score_registry_agent({"osu", "tuition"}, agent)
        assert score == 0

    def test_case_insensitive_match(self):
        agent = self._agent("OSU EXPERT", "")
        score = _score_registry_agent({"osu"}, agent)
        assert score == 1

    def test_tools_field_included_in_search(self):
        agent = self._agent("Some Agent", "", tools=["osu_lookup"])
        score = _score_registry_agent({"osu_lookup"}, agent)
        assert score == 1

    def test_partial_word_not_counted(self):
        agent = self._agent("OSU Expert", "")
        score = _score_registry_agent({"osu_extra_word_not_in_name"}, agent)
        assert score == 0


# ─────────────────────────────────────────────────────────────────────────────
# 2. POST /message endpoint tests
# ─────────────────────────────────────────────────────────────────────────────

CHRIS_GEMINI_PATH = "open_webui.routers.chris.gemini_chat"
AGENTS_PATH = "open_webui.routers.chris.Agents"
CALL_A2A_PATH = "open_webui.routers.chris._call_agent_a2a"


class TestChrisMessageEndpoint:
    def setup_method(self):
        self.client = TestClient(_make_app())

    def post(self, message, history=None):
        body = {"message": message}
        if history:
            body["history"] = history
        return self.client.post("/api/v1/chris/message", json=body)

    # ── validation ──────────────────────────────────────────────────────────

    def test_empty_message_returns_400(self):
        assert self.post("   ").status_code == 400

    def test_blank_message_returns_400(self):
        assert self.post("").status_code == 400

    # ── no installed agents → direct Gemini answer ───────────────────────────

    @patch(AGENTS_PATH + ".get_agents", return_value=[])
    @patch(CHRIS_GEMINI_PATH, new_callable=AsyncMock, return_value="Hi! I'm Chris.")
    def test_no_agents_answers_directly(self, mock_gemini, _mock_agents):
        resp = self.post("Hello")
        assert resp.status_code == 200
        data = resp.json()
        assert data["routed_to"] is None
        assert data["agent_name"] is None
        assert data["response"] == "Hi! I'm Chris."

    # ── routing to an installed agent ────────────────────────────────────────

    @patch(AGENTS_PATH + ".get_agents")
    @patch(CHRIS_GEMINI_PATH, new_callable=AsyncMock, return_value="osu-agent")
    @patch(CALL_A2A_PATH, return_value="OSU tuition is $12k/year.")
    def test_routes_to_matching_agent(self, mock_a2a, _mock_gemini, mock_agents):
        mock_agents.return_value = [_make_agent(id="osu-agent", name="OSU Expert")]

        resp = self.post("What is OSU tuition?")
        assert resp.status_code == 200
        data = resp.json()
        assert data["routed_to"] == "osu-agent"
        assert data["agent_name"] == "OSU Expert"
        assert data["response"] == "OSU tuition is $12k/year."
        mock_a2a.assert_called_once()

    @patch(AGENTS_PATH + ".get_agents")
    @patch(CHRIS_GEMINI_PATH, new_callable=AsyncMock)
    def test_gemini_says_none_falls_back_to_direct(self, mock_gemini, mock_agents):
        mock_agents.return_value = [_make_agent()]
        mock_gemini.side_effect = ["none", "Here is a direct answer."]

        resp = self.post("What's 2+2?")
        assert resp.status_code == 200
        data = resp.json()
        assert data["routed_to"] is None
        assert data["response"] == "Here is a direct answer."

    @patch(AGENTS_PATH + ".get_agents")
    @patch(CHRIS_GEMINI_PATH, new_callable=AsyncMock)
    def test_unknown_agent_id_from_gemini_falls_back_to_direct(self, mock_gemini, mock_agents):
        """Gemini hallucinated an agent id that doesn't exist — must answer directly."""
        mock_agents.return_value = [_make_agent(id="real-agent")]
        mock_gemini.side_effect = ["ghost-agent-id", "Direct fallback."]

        resp = self.post("Some question")
        assert resp.status_code == 200
        assert resp.json()["routed_to"] is None

    # ── agent failure → fallback ──────────────────────────────────────────────

    @patch(AGENTS_PATH + ".get_agents")
    @patch(CHRIS_GEMINI_PATH, new_callable=AsyncMock)
    @patch(CALL_A2A_PATH, side_effect=Exception("Connection refused"))
    def test_unreachable_agent_falls_back_to_direct(self, _mock_a2a, mock_gemini, mock_agents):
        mock_agents.return_value = [_make_agent(id="broken-agent")]
        mock_gemini.side_effect = ["broken-agent", "Fallback direct answer."]

        resp = self.post("Tell me about OSU")
        assert resp.status_code == 200
        data = resp.json()
        assert data["routed_to"] is None
        assert data["response"] == "Fallback direct answer."

    # ── Gemini down → 503 ─────────────────────────────────────────────────────

    @patch(AGENTS_PATH + ".get_agents", return_value=[])
    @patch(CHRIS_GEMINI_PATH, new_callable=AsyncMock, side_effect=Exception("Gemini down"))
    def test_gemini_unavailable_returns_503(self, _mock_gemini, _mock_agents):
        resp = self.post("Hello")
        assert resp.status_code == 503

    # ── Chris excluded from routing candidates ────────────────────────────────

    @patch(AGENTS_PATH + ".get_agents")
    @patch(CHRIS_GEMINI_PATH, new_callable=AsyncMock)
    def test_chris_itself_excluded_from_candidates(self, mock_gemini, mock_agents):
        """The Chris system agent must never appear as a routing target."""
        chris_agent = _make_agent(id="chris", name="Chris")
        real_agent = _make_agent(id="osu-agent", name="OSU Expert")
        mock_agents.return_value = [chris_agent, real_agent]
        mock_gemini.side_effect = ["none", "Direct."]

        self.post("Hi")

        # The routing prompt passed to Gemini should NOT include chris
        routing_call_messages = mock_gemini.call_args_list[0][0][0]
        routing_prompt = str(routing_call_messages)
        assert "osu-agent" in routing_prompt
        # 'chris' appears only as a system prompt name, not as a routable agent
        assert routing_prompt.count("id='chris'") == 0

    # ── history is forwarded to direct call ──────────────────────────────────

    @patch(AGENTS_PATH + ".get_agents", return_value=[])
    @patch(CHRIS_GEMINI_PATH, new_callable=AsyncMock, return_value="Reply.")
    def test_history_passed_to_gemini(self, mock_gemini, _mock_agents):
        self.post(
            "Follow up",
            history=[
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "First reply"},
            ],
        )
        call_messages = mock_gemini.call_args[0][0]
        roles = [m["role"] for m in call_messages]
        assert "user" in roles
        assert "assistant" in roles


# ─────────────────────────────────────────────────────────────────────────────
# 3. GET /suggestions endpoint tests
# ─────────────────────────────────────────────────────────────────────────────

REGISTRY_PATH = "open_webui.routers.chris.RegistryAgents"


class TestChrisSuggestionsEndpoint:
    def setup_method(self):
        self.client = TestClient(_make_app())

    def get(self, q="", limit=None):
        params = {}
        if q:
            params["q"] = q
        if limit is not None:
            params["limit"] = limit
        return self.client.get("/api/v1/chris/suggestions", params=params)

    # ── no query → newest first ───────────────────────────────────────────────

    @patch(AGENTS_PATH + ".get_agents", return_value=[])
    @patch(REGISTRY_PATH + ".get_agents_by_user_id")
    def test_no_query_returns_newest_agents(self, mock_registry, _installed):
        mock_registry.return_value = [
            _make_registry_agent("a1", "Agent A", created_at=100),
            _make_registry_agent("a2", "Agent B", created_at=300),
            _make_registry_agent("a3", "Agent C", created_at=50),
        ]
        resp = self.get()
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.json()]
        assert ids[0] == "a2"  # highest created_at first

    # ── scored by query ───────────────────────────────────────────────────────

    @patch(AGENTS_PATH + ".get_agents", return_value=[])
    @patch(REGISTRY_PATH + ".get_agents_by_user_id")
    def test_query_returns_best_matching_first(self, mock_registry, _installed):
        mock_registry.return_value = [
            _make_registry_agent("weather", "Weather Bot", "weather forecasts rain"),
            _make_registry_agent("osu", "OSU Expert", "osu university admissions"),
            _make_registry_agent("chef", "Chef Bot", "cooking recipes"),
        ]
        resp = self.get(q="osu university")
        assert resp.status_code == 200
        assert resp.json()[0]["id"] == "osu"

    # ── already-installed agents filtered ────────────────────────────────────

    @patch(AGENTS_PATH + ".get_agents")
    @patch(REGISTRY_PATH + ".get_agents_by_user_id")
    def test_installed_agents_filtered_by_id(self, mock_registry, mock_installed):
        mock_installed.return_value = [_make_agent(id="installed-1", url="http://x/")]
        mock_registry.return_value = [
            _make_registry_agent("installed-1", "Installed", url="http://x/"),
            _make_registry_agent("new-agent", "New Agent", url="http://new/"),
        ]
        resp = self.get()
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.json()]
        assert "installed-1" not in ids
        assert "new-agent" in ids

    @patch(AGENTS_PATH + ".get_agents")
    @patch(REGISTRY_PATH + ".get_agents_by_user_id")
    def test_installed_agents_filtered_by_url(self, mock_registry, mock_installed):
        """Filter by URL catches agents registered via URL even if IDs differ."""
        mock_installed.return_value = [_make_agent(id="local-id", url="http://shared-url/")]
        mock_registry.return_value = [
            _make_registry_agent("registry-id", "Shared Agent", url="http://shared-url/"),
            _make_registry_agent("other", "Other Agent", url="http://other/"),
        ]
        resp = self.get()
        ids = [r["id"] for r in resp.json()]
        assert "registry-id" not in ids
        assert "other" in ids

    # ── limit respected ───────────────────────────────────────────────────────

    @patch(AGENTS_PATH + ".get_agents", return_value=[])
    @patch(REGISTRY_PATH + ".get_agents_by_user_id")
    def test_default_limit_is_three(self, mock_registry, _installed):
        mock_registry.return_value = [
            _make_registry_agent(f"a{i}", f"Agent {i}", created_at=i)
            for i in range(10)
        ]
        resp = self.get()
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    @patch(AGENTS_PATH + ".get_agents", return_value=[])
    @patch(REGISTRY_PATH + ".get_agents_by_user_id")
    def test_custom_limit_respected(self, mock_registry, _installed):
        mock_registry.return_value = [
            _make_registry_agent(f"a{i}", f"Agent {i}", created_at=i)
            for i in range(10)
        ]
        resp = self.get(limit=5)
        assert resp.status_code == 200
        assert len(resp.json()) == 5

    @patch(AGENTS_PATH + ".get_agents", return_value=[])
    @patch(REGISTRY_PATH + ".get_agents_by_user_id", return_value=[])
    def test_empty_registry_returns_empty_list(self, _registry, _installed):
        resp = self.get()
        assert resp.status_code == 200
        assert resp.json() == []
