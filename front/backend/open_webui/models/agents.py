import time
from typing import Any, Optional, List

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import BigInteger, Column, String, Text, Boolean

from open_webui.internal.db import Base, JSONField, get_db
from open_webui.utils.access_control import has_access

####################
# Agent DB Schema
####################


class Agent(Base):
    __tablename__ = "agent"

    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(Text)
    endpoint = Column(String, nullable=True)

    # A2A Protocol fields
    url = Column(String, nullable=True)
    version = Column(String, nullable=True)
    capabilities = Column(JSONField, nullable=True)
    skills = Column(JSONField, nullable=True)
    default_input_modes = Column(JSONField, nullable=True)
    default_output_modes = Column(JSONField, nullable=True)

    # Schema fields for validation
    input_schema = Column(JSONField, nullable=True)
    output_schema = Column(JSONField, nullable=True)
    profile_image_url = Column(Text, nullable=True)

    # Deploy-view fields (internal-runtime agents)
    system_prompt = Column(Text, nullable=True)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    deployment_mode = Column(String, nullable=True)
    deployment_status = Column(String, nullable=True)
    cloud_run_auth_required = Column(Boolean, default=False)

    # Access control
    access_control = Column(JSONField, nullable=True)
    # - `None`: public to all authenticated users
    # - `{}`: private to owner/admin only
    # - Custom permissions: {"read": {...}, "write": {...}}

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)

    # User who registered the agent
    user_id = Column(String, nullable=True)


class AgentModel(BaseModel):
    id: str
    name: str
    description: str
    endpoint: Optional[str] = None
    url: Optional[str] = None
    version: Optional[str] = None
    capabilities: Optional[dict] = None
    skills: Optional[List[dict]] = None
    default_input_modes: Optional[List[str]] = None
    default_output_modes: Optional[List[str]] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    profile_image_url: Optional[str] = None
    system_prompt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    deployment_mode: Optional[str] = None
    deployment_status: Optional[str] = None
    cloud_run_auth_required: bool = False
    access_control: Optional[dict] = None
    is_active: bool = True
    created_at: int
    updated_at: int
    user_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

####################
# Forms
####################


class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    endpoint: Optional[str] = None
    url: Optional[str] = None
    capabilities: Optional[dict] = None
    skills: Optional[List[dict]] = None
    profile_image_url: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    deployment_mode: Optional[str] = None
    deployment_status: Optional[str] = None
    cloud_run_auth_required: bool = False
    access_control: Optional[dict] = None
    user_id: Optional[str] = None
    is_active: bool = True


class RegisterAgentForm(BaseModel):
    name: str
    description: str
    endpoint: Optional[str] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    access_control: Optional[dict] = Field(default_factory=dict)


class RegisterAgentByUrlForm(BaseModel):
    agent_url: str
    profile_image_url: Optional[str] = None
    access_control: Optional[dict] = Field(default_factory=dict)


class AgentUpdateForm(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    endpoint: Optional[str] = None
    access_control: Optional[dict] = None
    is_active: Optional[bool] = None


class DeployAgentForm(BaseModel):
    name: str
    description: str
    system_prompt: str
    provider: str = "anthropic"
    model: Optional[str] = None
    profile_image_url: Optional[str] = None
    access_control: Optional[dict] = Field(default_factory=dict)
    publish_to_registry: bool = False
    deploy_to_cloud_run: bool = False
    cloud_run_public: bool = False

    model_config = ConfigDict(protected_namespaces=())


####################
# Agent Table
####################


_UNSET = object()


class AgentsTable:
    def insert_new_agent(
        self,
        id: str,
        name: str,
        description: str,
        endpoint: Optional[str] = None,
        url: Optional[str] = None,
        version: Optional[str] = None,
        capabilities: Optional[dict] = None,
        skills: Optional[List[dict]] = None,
        default_input_modes: Optional[List[str]] = None,
        default_output_modes: Optional[List[str]] = None,
        input_schema: Optional[dict] = None,
        output_schema: Optional[dict] = None,
        profile_image_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        deployment_mode: Optional[str] = None,
        deployment_status: Optional[str] = None,
        cloud_run_auth_required: bool = False,
        access_control: Any = _UNSET,
        user_id: Optional[str] = None,
    ) -> Optional[AgentModel]:
        """Insert a new A2A agent row."""
        resolved_access_control = {} if access_control is _UNSET else access_control
        with get_db() as db:
            agent = AgentModel(
                **{
                    "id": id,
                    "name": name,
                    "description": description,
                    "endpoint": endpoint,
                    "url": url,
                    "version": version,
                    "capabilities": capabilities,
                    "skills": skills,
                    "default_input_modes": default_input_modes,
                    "default_output_modes": default_output_modes,
                    "input_schema": input_schema,
                    "output_schema": output_schema,
                    "profile_image_url": profile_image_url,
                    "system_prompt": system_prompt,
                    "provider": provider,
                    "model": model,
                    "deployment_mode": deployment_mode,
                    "deployment_status": deployment_status,
                    "cloud_run_auth_required": cloud_run_auth_required,
                    "access_control": resolved_access_control,
                    "is_active": True,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                    "user_id": user_id,
                }
            )

            result = Agent(**agent.model_dump())
            db.add(result)
            db.commit()
            db.refresh(result)
            return AgentModel.model_validate(result) if result else None

    def get_agent_by_id(self, id: str) -> Optional[AgentModel]:
        """Return an agent by ID."""
        try:
            with get_db() as db:
                agent = db.query(Agent).filter_by(id=id).first()
                return AgentModel.model_validate(agent) if agent else None
        except Exception:
            return None

    def get_agent_by_url(self, url: str) -> Optional[AgentModel]:
        """Return an agent by public URL."""
        try:
            with get_db() as db:
                agent = db.query(Agent).filter_by(url=url).first()
                return AgentModel.model_validate(agent) if agent else None
        except Exception:
            return None

    def get_agents(self) -> List[AgentModel]:
        """Return all active agents."""
        with get_db() as db:
            agents = db.query(Agent).filter_by(is_active=True).all()
            return [AgentModel.model_validate(agent) for agent in agents]

    def get_agents_by_user_id(
        self, user_id: str, permission: str = "read"
    ) -> List[AgentModel]:
        """Return active agents visible to a user."""
        return [
            agent
            for agent in self.get_agents()
            if agent.user_id == user_id
            or has_access(user_id, permission, agent.access_control)
        ]

    def get_all_agents(self) -> List[AgentModel]:
        """Return all agents regardless of active state."""
        with get_db() as db:
            agents = db.query(Agent).all()
            return [AgentModel.model_validate(agent) for agent in agents]

    def update_agent_by_id(
        self, id: str, updated: AgentUpdateForm
    ) -> Optional[AgentModel]:
        """Update mutable agent fields by ID."""
        try:
            with get_db() as db:
                agent = db.query(Agent).filter_by(id=id).first()
                if not agent:
                    return None

                update_data = updated.model_dump(exclude_unset=True)
                update_data["updated_at"] = int(time.time())

                for key, value in update_data.items():
                    setattr(agent, key, value)

                db.commit()
                db.refresh(agent)
                return AgentModel.model_validate(agent)
        except Exception:
            return None

    def delete_agent_by_id(self, id: str) -> bool:
        """Delete an agent by ID."""
        try:
            with get_db() as db:
                agent = db.query(Agent).filter_by(id=id).first()
                if not agent:
                    return False
                db.delete(agent)
                db.commit()
                return True
        except Exception:
            return False

    def update_agent_metadata_by_id(
        self, id: str, updated: dict
    ) -> Optional[AgentModel]:
        """Update A2A card-derived metadata for an agent."""
        try:
            with get_db() as db:
                agent = db.query(Agent).filter_by(id=id).first()
                if not agent:
                    return None

                allowed_keys = {
                    "name",
                    "description",
                    "version",
                    "capabilities",
                    "skills",
                    "default_input_modes",
                    "default_output_modes",
                    "profile_image_url",
                }
                update_data = {
                    key: value
                    for key, value in updated.items()
                    if key in allowed_keys
                }
                update_data["updated_at"] = int(time.time())

                for key, value in update_data.items():
                    setattr(agent, key, value)

                db.commit()
                db.refresh(agent)
                return AgentModel.model_validate(agent)
        except Exception:
            return None


Agents = AgentsTable()
