from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, List
from datetime import datetime
import uuid

class IntegrationBase(BaseModel):
    """Base model for all integrations"""
    type: str
    name: str
    status: Literal["active", "inactive", "pending", "error"] = "inactive"
    userId: str
    chatbotId: Optional[str] = None
    config: Dict[str, Any] = {}
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class SlackIntegrationConfig(BaseModel):
    """Configuration for Slack integration"""
    webhookUrl: str
    botToken: Optional[str] = None
    signingSecret: Optional[str] = None
    appId: Optional[str] = None
    clientId: Optional[str] = None
    clientSecret: Optional[str] = None
    teamId: Optional[str] = None
    channelId: Optional[str] = None
    botUserId: Optional[str] = None

class WebsiteIntegrationConfig(BaseModel):
    """Configuration for Website integration (custom domains)"""
    domain: str
    verified: bool = False
    verificationToken: Optional[str] = None

# Request models
class IntegrationCreate(BaseModel):
    """Model for creating a new integration"""
    type: Literal["slack", "website"]
    name: str
    chatbotId: Optional[str] = None
    config: Dict[str, Any]

class IntegrationUpdate(BaseModel):
    """Model for updating an integration"""
    name: Optional[str] = None
    status: Optional[Literal["active", "inactive", "pending"]] = None
    chatbotId: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

# Response models
class Integration(IntegrationBase):
    """Complete integration model with ID"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SlackIntegration(Integration):
    """Slack integration model"""
    type: Literal["slack"] = "slack"
    config: SlackIntegrationConfig

class WebsiteIntegration(Integration):
    """Website integration model"""
    type: Literal["website"] = "website"
    config: WebsiteIntegrationConfig

class SlackEventPayload(BaseModel):
    """Model for Slack event payloads"""
    type: str
    token: Optional[str] = None
    challenge: Optional[str] = None
    team_id: Optional[str] = None
    api_app_id: Optional[str] = None
    event: Optional[Dict[str, Any]] = None
    event_id: Optional[str] = None
    event_time: Optional[int] = None
    authorizations: Optional[List[Dict[str, Any]]] = None 