"""
conftest.py — lightweight stubs for Chris router unit tests.

Intercepts open_webui's import chain before it hits the DB or heavy ML deps,
replacing only what the Chris router actually needs at import time.
All stubs are set up as module-level sys.modules entries so they're in place
before test_chris.py is collected.
"""

import os
import sys
import types
from typing import Any, Optional, List
from unittest.mock import AsyncMock, MagicMock

# ── 1. env vars (must be set before any open_webui import) ───────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/test_chris.db")
os.environ.setdefault("WEBUI_SECRET_KEY", "test-unit-secret")
os.environ.setdefault("SECRET_KEY", "test-unit-secret")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("CHRIS_MODEL", "gemini-2.5-flash-lite")

# ── 2. backend on sys.path ────────────────────────────────────────────────────
_BACKEND = os.path.abspath(
    os.path.join(os.path.dirname(__file__), *[".."] * 5, "backend")
)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# ── helper ────────────────────────────────────────────────────────────────────
def _stub(name: str, **attrs) -> MagicMock:
    """Create and register a MagicMock module in sys.modules."""
    m = MagicMock()
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


# ── 3. heavy third-party packages ────────────────────────────────────────────
for _pkg in [
    "typer", "uvicorn", "uvicorn.config", "uvicorn.main",
    "aiocache", "aiocache.backends", "aiocache.backends.memory",
    "aiohttp", "aiofiles",
    "peewee_migrate",
    "boto3", "botocore", "botocore.exceptions",
    "google.generativeai",
    "anthropic",
    "chromadb", "langchain_text_splitters",
    "sentence_transformers",
    "docx2txt", "pypdf", "openpyxl", "xlrd", "pptx", "ebooklib",
    "cv2", "soundfile", "pyaudio", "faster_whisper",
    "msal", "ldap3",
    "validators", "bs4", "ftfy", "Levenshtein",
    "socketio", "engineio",
    "opentelemetry", "opentelemetry.sdk", "opentelemetry.sdk.trace",
    "opentelemetry.trace", "opentelemetry.instrumentation",
    "opentelemetry.instrumentation.fastapi",
    "redis", "redis.asyncio",
    "markdown", "duckdb",
]:
    sys.modules.setdefault(_pkg, MagicMock())

# ── 4. open_webui.config — fake module, no DB query ──────────────────────────
_cfg = types.ModuleType("open_webui.config")
_cfg.GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
_cfg.CHRIS_MODEL = os.environ["CHRIS_MODEL"]
_cfg.SECRET_KEY = os.environ["SECRET_KEY"]
_cfg.WEBUI_SECRET_KEY = os.environ["WEBUI_SECRET_KEY"]
_cfg.DATABASE_URL = os.environ["DATABASE_URL"]
_cfg.DEFAULT_USER_PERMISSIONS = {}
_cfg.DEFAULT_MODELS = MagicMock()
_cfg.DEFAULT_MODELS.value = ""
_cfg.ENABLE_COMMUNITY_SHARING = MagicMock()
# anything else config.py exports — satisfy with MagicMock attributes
_cfg.__getattr__ = lambda name: MagicMock()  # type: ignore[assignment]
sys.modules["open_webui.config"] = _cfg

# ── 5. open_webui.env — fake module ──────────────────────────────────────────
_env = types.ModuleType("open_webui.env")
_env.SRC_LOG_LEVELS = {"MAIN": "WARNING", "MODELS": "WARNING", "APPS": "WARNING"}
_env.GLOBAL_LOG_LEVEL = "WARNING"
_env.BYPASS_MODEL_ACCESS_CONTROL = False
sys.modules["open_webui.env"] = _env

# ── 6. open_webui.constants ───────────────────────────────────────────────────
_const = types.ModuleType("open_webui.constants")
_const.ERROR_MESSAGES = MagicMock()
sys.modules["open_webui.constants"] = _const

# ── 7. heavy internal modules we don't need ──────────────────────────────────
for _sub in [
    "open_webui.internal",
    "open_webui.internal.db",
    "open_webui.internal.wrappers",
    "open_webui.socket",
    "open_webui.socket.main",
    "open_webui.functions",
    "open_webui.retrieval",
    "open_webui.retrieval.vector",
    "open_webui.retrieval.vector.main",
    "open_webui.utils.access_control",
    "open_webui.utils.plugin",
    "open_webui.utils.models",
    "open_webui.utils.payload",
    "open_webui.utils.response",
    "open_webui.utils.filter",
    "open_webui.utils.misc",
    "open_webui.utils.webhook",
    "open_webui.routers.audio",
    "open_webui.routers.images",
    "open_webui.routers.ollama",
    "open_webui.routers.openai",
    "open_webui.routers.pipelines",
    "open_webui.routers.rag",
    "open_webui.routers.webui",
    "open_webui.routers.knowledge",
]:
    sys.modules.setdefault(_sub, MagicMock())

# ── 7b. open_webui.utils.encryption — stub with no-op functions ──────────────
_enc_mod = types.ModuleType("open_webui.utils.encryption")
_enc_mod.ENABLE_CHAT_ENCRYPTION = False
_enc_mod.create_user_key_ref = MagicMock(return_value=None)
_enc_mod.encrypt_chat_content = MagicMock(return_value=(b"", b""))
_enc_mod.decrypt_chat_content = MagicMock(return_value={})
sys.modules["open_webui.utils.encryption"] = _enc_mod

# ── 8. fake open_webui.models.agents ─────────────────────────────────────────
from pydantic import BaseModel as _BaseModel


class AgentModel(_BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    endpoint: Optional[str] = None
    url: Optional[str] = None
    skills: Optional[List[Any]] = None
    capabilities: Optional[dict] = None
    version: Optional[str] = None
    profile_image_url: Optional[str] = None
    user_id: Optional[str] = None
    is_active: bool = True
    created_at: int = 0


class Agents:
    """In-memory agent store for tests."""
    _store: List[AgentModel] = []

    @classmethod
    def get_agents(cls) -> List[AgentModel]:
        return list(cls._store)

    @classmethod
    def get_agent_by_id(cls, agent_id: str) -> Optional[AgentModel]:
        return next((a for a in cls._store if a.id == agent_id), None)

    @classmethod
    def insert_new_agent(cls, **kwargs) -> AgentModel:
        valid = {k: v for k, v in kwargs.items() if k in AgentModel.model_fields}
        agent = AgentModel(**valid)
        cls._store.append(agent)
        return agent

    @classmethod
    def _reset(cls) -> None:
        cls._store = []


class AgentResponse(_BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    endpoint: Optional[str] = None
    url: Optional[str] = None
    trust_tier: Optional[str] = "public"
    required_role: Optional[str] = None


class RegisterAgentForm(_BaseModel):
    name: str
    url: Optional[str] = None
    endpoint: Optional[str] = None
    trust_tier: str = "public"
    required_role: Optional[str] = None


class RegisterAgentByUrlForm(_BaseModel):
    url: str
    trust_tier: str = "public"
    required_role: Optional[str] = None


class AgentUpdateForm(_BaseModel):
    trust_tier: Optional[str] = None
    required_role: Optional[str] = None


class DeployAgentForm(_BaseModel):
    trust_tier: str = "public"
    required_role: Optional[str] = None


_agents_mod = types.ModuleType("open_webui.models.agents")
_agents_mod.AgentModel = AgentModel
_agents_mod.AgentResponse = AgentResponse
_agents_mod.RegisterAgentForm = RegisterAgentForm
_agents_mod.RegisterAgentByUrlForm = RegisterAgentByUrlForm
_agents_mod.AgentUpdateForm = AgentUpdateForm
_agents_mod.DeployAgentForm = DeployAgentForm
_agents_mod.Agents = Agents
_agents_mod._Agents = Agents  # alias used by test file
sys.modules["open_webui.models.agents"] = _agents_mod

# ── 9. fake open_webui.models.registry ───────────────────────────────────────
class RegistryAgents:
    """In-memory registry agent store for tests."""
    _store: list = []

    @classmethod
    def get_agents_by_user_id(cls, user_id: str, permission: str = "read") -> list:
        return list(cls._store)

    @classmethod
    def _reset(cls) -> None:
        cls._store = []


_registry_mod = types.ModuleType("open_webui.models.registry")
_registry_mod.RegistryAgents = RegistryAgents
_registry_mod._RegistryAgents = RegistryAgents  # alias used by test file
sys.modules["open_webui.models.registry"] = _registry_mod

# ── 10. fake open_webui.utils.auth — expose get_verified_user ────────────────
_auth_mod = types.ModuleType("open_webui.utils.auth")

async def get_verified_user():
    """Placeholder — tests override via app.dependency_overrides."""
    from fastapi import HTTPException
    raise HTTPException(status_code=401, detail="Not authenticated")

async def get_admin_user():
    raise get_verified_user()

async def get_current_user():
    raise get_verified_user()

def get_optional_user():
    return None

def decode_token(token: str) -> Optional[dict]:
    return None

_auth_mod.get_verified_user = get_verified_user
_auth_mod.get_admin_user = get_admin_user
_auth_mod.get_current_user = get_current_user
_auth_mod.get_optional_user = get_optional_user
_auth_mod.decode_token = decode_token
# create_token and decode_token are also used by routers/chats.py
_auth_mod.create_token = MagicMock(return_value="stub-token")
sys.modules["open_webui.utils.auth"] = _auth_mod

# Pre-register open_webui.utils.privacy using the real source file so that
# test_privacy.py can import extract_source_domain even when open_webui.utils
# is later overwritten with a MagicMock (which prevents normal filesystem imports).
import importlib.util as _importlib_util
_privacy_path = os.path.join(_BACKEND, "open_webui", "utils", "privacy.py")
if os.path.exists(_privacy_path):
    _privacy_spec = _importlib_util.spec_from_file_location(
        "open_webui.utils.privacy", _privacy_path
    )
    _privacy_real = _importlib_util.module_from_spec(_privacy_spec)
    sys.modules["open_webui.utils.privacy"] = _privacy_real
    _privacy_spec.loader.exec_module(_privacy_real)

sys.modules.setdefault("open_webui.utils", MagicMock())

# ── 10b. fake open_webui.models.chats — minimal stubs for import ─────────────
for _m in [
    "open_webui.models.chats",
    "open_webui.models.tags",
    "open_webui.models.folders",
    "open_webui.models.groups",
    "open_webui.models.users",
]:
    sys.modules.setdefault(_m, MagicMock())

# ── 11. fake open_webui.utils.a2a_runtime ────────────────────────────────────
_a2a_runtime_mod = types.ModuleType("open_webui.utils.a2a_runtime")
_a2a_runtime_mod.PROVIDER_DEFAULTS = {"anthropic": "claude-sonnet-4-6"}
_a2a_runtime_mod.run_agent_turn = AsyncMock(return_value="stub reply")
sys.modules["open_webui.utils.a2a_runtime"] = _a2a_runtime_mod

# ── 12. fake open_webui.utils.chris_gemini ───────────────────────────────────
_gemini_mod = types.ModuleType("open_webui.utils.chris_gemini")
_gemini_mod.chat = AsyncMock(return_value="stubbed gemini response")
sys.modules["open_webui.utils.chris_gemini"] = _gemini_mod
