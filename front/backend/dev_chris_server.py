"""
Minimal dev server for testing the Chris orchestrator router locally.

Stubs out all heavy open_webui dependencies (ML, PostgreSQL, etc.) so the
server starts with nothing but uvicorn + fastapi + openai installed.
Uses in-memory agent storage — agents reset on restart.

Usage:
    cd front/backend
    GEMINI_API_KEY=<your_key> python dev_chris_server.py

Then browse to http://localhost:8765/docs for the Swagger UI.

Dev auth: every request is auto-authenticated as dev-user@example.com (role=admin).
No real login required.
"""

import os
import sys
import types
from typing import Any, Optional, List
from unittest.mock import MagicMock, AsyncMock

# ── 1. env defaults ────────────────────────────────────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/openbeavs_dev.db")
os.environ.setdefault("WEBUI_SECRET_KEY", "dev-only-secret")
os.environ.setdefault("SECRET_KEY", "dev-only-secret")
os.environ.setdefault("GEMINI_API_KEY", "")  # override via env
os.environ.setdefault("CHRIS_MODEL", "gemini-2.5-flash-lite")

# ── 2. backend on sys.path ────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# ── 3. stub heavy packages ─────────────────────────────────────────────────────
for _pkg in [
    "typer",
    # NOTE: do NOT stub uvicorn.config / uvicorn.main — we actually call uvicorn.run() here.
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
    "markdown", "duckdb",
]:
    sys.modules.setdefault(_pkg, MagicMock())

# ── 4. fake open_webui.config ──────────────────────────────────────────────────
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
# Module-level __getattr__ receives only the attribute name (no self).
_cfg.__getattr__ = lambda name: MagicMock()  # type: ignore[assignment]
sys.modules["open_webui.config"] = _cfg

# ── 5. fake open_webui.env ─────────────────────────────────────────────────────
_env = types.ModuleType("open_webui.env")
_env.SRC_LOG_LEVELS = {"MAIN": "INFO", "APPS": "INFO"}
_env.GLOBAL_LOG_LEVEL = "INFO"
_env.BYPASS_MODEL_ACCESS_CONTROL = False
sys.modules["open_webui.env"] = _env

# ── 6. fake open_webui.constants ──────────────────────────────────────────────
_const = types.ModuleType("open_webui.constants")
_const.ERROR_MESSAGES = MagicMock()
sys.modules["open_webui.constants"] = _const

# ── 7. stub heavy internal modules ────────────────────────────────────────────
for _sub in [
    "open_webui.internal", "open_webui.internal.db", "open_webui.internal.wrappers",
    "open_webui.socket", "open_webui.socket.main",
    "open_webui.functions",
    "open_webui.retrieval", "open_webui.retrieval.vector",
    "open_webui.retrieval.vector.main",
    "open_webui.utils.access_control", "open_webui.utils.plugin",
    "open_webui.utils.models", "open_webui.utils.payload",
    "open_webui.utils.response", "open_webui.utils.filter",
    "open_webui.routers.audio", "open_webui.routers.images",
    "open_webui.routers.ollama", "open_webui.routers.openai",
    "open_webui.routers.pipelines", "open_webui.routers.rag",
    "open_webui.routers.webui", "open_webui.routers.knowledge",
]:
    sys.modules.setdefault(_sub, MagicMock())

# ── 8. in-memory agent store ──────────────────────────────────────────────────
from pydantic import BaseModel as _PydanticBase


class AgentModel(_PydanticBase):
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


_AGENT_STORE: List[AgentModel] = []


class Agents:
    @classmethod
    def get_agents(cls) -> List[AgentModel]:
        return list(_AGENT_STORE)

    @classmethod
    def get_agent_by_id(cls, agent_id: str) -> Optional[AgentModel]:
        return next((a for a in _AGENT_STORE if a.id == agent_id), None)

    @classmethod
    def insert_new_agent(cls, **kwargs) -> AgentModel:
        valid = {k: v for k, v in kwargs.items() if k in AgentModel.model_fields}
        agent = AgentModel(**valid)
        _AGENT_STORE.append(agent)
        return agent


_agents_mod = types.ModuleType("open_webui.models.agents")
_agents_mod.AgentModel = AgentModel
_agents_mod.Agents = Agents
sys.modules["open_webui.models.agents"] = _agents_mod

# ── 9. in-memory registry store ───────────────────────────────────────────────
_REGISTRY_STORE: list = []


class RegistryAgents:
    @classmethod
    def get_agents_by_user_id(cls, user_id: str, permission: str = "read") -> list:
        return list(_REGISTRY_STORE)


_registry_mod = types.ModuleType("open_webui.models.registry")
_registry_mod.RegistryAgents = RegistryAgents
sys.modules["open_webui.models.registry"] = _registry_mod

# ── 10. dev auth — auto-login, no real JWT ────────────────────────────────────
_auth_mod = types.ModuleType("open_webui.utils.auth")


class _DevUser:
    id = "dev-user-1"
    email = "dev@openbeavs.local"
    role = "admin"
    name = "Dev User"


async def get_verified_user():
    return _DevUser()


async def get_admin_user():
    return _DevUser()


async def get_current_user():
    return _DevUser()


_auth_mod.get_verified_user = get_verified_user
_auth_mod.get_admin_user = get_admin_user
_auth_mod.get_current_user = get_current_user
sys.modules["open_webui.utils.auth"] = _auth_mod
# NOTE: do NOT stub "open_webui.utils" itself — we need it as a real package
# so that open_webui.utils.chris_gemini can be imported below.

# ── 11. real Gemini wrapper ────────────────────────────────────────────────────
# Import after stubs are in place so open_webui.config is resolved correctly.
from open_webui.utils.chris_gemini import chat as _gemini_chat  # noqa: E402

_gemini_mod = types.ModuleType("open_webui.utils.chris_gemini")
_gemini_mod.chat = _gemini_chat
sys.modules["open_webui.utils.chris_gemini"] = _gemini_mod

# ── 12. build the FastAPI app ──────────────────────────────────────────────────
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from open_webui.routers.chris import router as chris_router  # noqa: E402

app = FastAPI(
    title="Chris Dev Server",
    description=(
        "Minimal dev harness for the Chris orchestrator.\n\n"
        "**All requests are auto-authenticated as dev@openbeavs.local (admin).**\n\n"
        "Agents are stored in-memory and reset on restart."
    ),
    version="dev",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chris_router, prefix="/api/v1/chris", tags=["Chris"])


# ── 13. convenience agent management endpoints ────────────────────────────────
import uuid as _uuid
import requests as _req


@app.get("/api/agents", summary="List installed agents")
def list_agents():
    return [a.model_dump() for a in _AGENT_STORE]


@app.post("/api/agents/register-by-url", summary="Register agent by well-known URL")
def register_by_url(body: dict):
    """Fetch the agent card from /.well-known/agent.json and register it."""
    url: str = body.get("url", "").rstrip("/")
    if not url:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="url is required")

    card_url = url if url.endswith("agent.json") else f"{url}/.well-known/agent.json"
    try:
        card = _req.get(card_url, timeout=10).json()
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=502, detail=f"Could not fetch agent card: {e}")

    agent_id = card.get("name", "").lower().replace(" ", "-") or str(_uuid.uuid4())
    # Avoid duplicates
    existing = Agents.get_agent_by_id(agent_id)
    if existing:
        return {"status": "already registered", "agent": existing.model_dump()}

    agent = Agents.insert_new_agent(
        id=agent_id,
        name=card.get("name", agent_id),
        description=card.get("description"),
        url=card.get("url", url),
        endpoint=card.get("url", url),
        version=card.get("version"),
        skills=card.get("skills"),
        capabilities=card.get("capabilities"),
        created_at=0,
    )
    return {"status": "registered", "agent": agent.model_dump()}


@app.delete("/api/agents/{agent_id}", summary="Remove an agent")
def remove_agent(agent_id: str):
    global _AGENT_STORE
    before = len(_AGENT_STORE)
    _AGENT_STORE[:] = [a for a in _AGENT_STORE if a.id != agent_id]
    return {"removed": before - len(_AGENT_STORE)}


if __name__ == "__main__":
    import uvicorn

    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("\n⚠️  GEMINI_API_KEY is not set — Chris will raise 503 on /message.\n"
              "    Set it: export GEMINI_API_KEY=<your_key>\n")

    print("\n Chris Dev Server")
    print(" ─────────────────────────────────────────────")
    print(" Swagger UI : http://localhost:8765/docs")
    print(" Chris chat : POST http://localhost:8765/api/v1/chris/message")
    print(" Agents     : GET  http://localhost:8765/api/agents")
    print(" Register   : POST http://localhost:8765/api/agents/register-by-url")
    print(" ─────────────────────────────────────────────\n")

    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")
