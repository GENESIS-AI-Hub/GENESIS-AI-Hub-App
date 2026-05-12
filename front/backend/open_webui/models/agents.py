import logging
import time
from typing import Literal, Optional, List
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy import BigInteger, Column, String, Text, Boolean, text
from sqlalchemy.exc import IntegrityError

from open_webui.internal.db import Base, JSONField, get_db, engine

log = logging.getLogger(__name__)

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

    # Trust tier — coarse access gate (public / authenticated / privileged)
    # TODO(#141/#143): replace role→tier mapping with real OSU OIDC scope claims
    trust_tier = Column(String, nullable=False, server_default=text("'public'"))
    required_role = Column(String, nullable=True)  # stored, not yet enforced (#141)

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
    trust_tier: Literal["public", "authenticated", "privileged"] = "public"
    required_role: Optional[str] = None
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
    trust_tier: Literal["public", "authenticated", "privileged"] = "public"
    required_role: Optional[str] = None
    is_active: bool = True


class RegisterAgentForm(BaseModel):
    name: str
    description: str
    endpoint: Optional[str] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    trust_tier: Literal["public", "authenticated", "privileged"] = "public"
    required_role: Optional[str] = None

    @model_validator(mode="after")
    def _validate_tier_role_pair(self) -> "RegisterAgentForm":
        if self.trust_tier == "public":
            self.required_role = None
        elif self.trust_tier == "privileged" and not self.required_role:
            raise ValueError(
                "required_role must be set when trust_tier is 'privileged'"
            )
        return self


class RegisterAgentByUrlForm(BaseModel):
    agent_url: str
    profile_image_url: Optional[str] = None


class AgentUpdateForm(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    endpoint: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None
    trust_tier: Optional[Literal["public", "authenticated", "privileged"]] = None
    required_role: Optional[str] = None


class DeployAgentForm(BaseModel):
    name: str
    description: str
    system_prompt: str
    provider: str = "anthropic"
    model: Optional[str] = None
    profile_image_url: Optional[str] = None
    publish_to_registry: bool = True
    deploy_to_cloud_run: bool = False
    trust_tier: Literal["public", "authenticated", "privileged"] = "public"
    required_role: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=())

    @model_validator(mode="after")
    def _validate_tier_role_pair(self) -> "DeployAgentForm":
        if self.trust_tier == "public":
            self.required_role = None
        elif self.trust_tier == "privileged" and not self.required_role:
            raise ValueError(
                "required_role must be set when trust_tier is 'privileged'"
            )
        return self


####################
# Agent Table
####################


class AgentsTable:
    def __init__(self):
        Agent.metadata.create_all(bind=engine)

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
        trust_tier: str = "public",
        required_role: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[AgentModel]:
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
                    "trust_tier": trust_tier,
                    "required_role": required_role,
                    "is_active": True,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                    "user_id": user_id,
                }
            )

            try:
                result = Agent(**agent.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                return AgentModel.model_validate(result) if result else None
            except IntegrityError as e:
                db.rollback()
                log.warning("agent insert failed (integrity): %s", e.orig)
                return None
            except Exception as e:
                db.rollback()
                log.exception("agent insert failed: %s", e)
                return None

    def get_agent_by_id(self, id: str) -> Optional[AgentModel]:
        try:
            with get_db() as db:
                agent = db.query(Agent).filter_by(id=id).first()
                return AgentModel.model_validate(agent) if agent else None
        except Exception:
            return None

    def get_agent_by_url(self, url: str) -> Optional[AgentModel]:
        try:
            with get_db() as db:
                agent = db.query(Agent).filter_by(url=url).first()
                return AgentModel.model_validate(agent) if agent else None
        except Exception:
            return None

    def get_agents(self) -> List[AgentModel]:
        with get_db() as db:
            agents = db.query(Agent).filter_by(is_active=True).all()
            return [AgentModel.model_validate(agent) for agent in agents]

    def get_all_agents(self) -> List[AgentModel]:
        with get_db() as db:
            agents = db.query(Agent).all()
            return [AgentModel.model_validate(agent) for agent in agents]

    def update_agent_by_id(
        self, id: str, updated: AgentUpdateForm
    ) -> Optional[AgentModel]:
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


Agents = AgentsTable()
