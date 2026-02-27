from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TrackEventRequest(BaseModel):
    device_id: Optional[str] = Field(default=None, description="device uuid")
    user_id: Optional[str] = Field(default=None, description="user uuid")
    agent_id: Optional[str] = Field(default=None, description="agent uuid")
    child_id: Optional[str] = Field(default=None, description="child uuid")
    device_network_type: Optional[str] = Field(default=None, description="device network type")
    mobile_system: Optional[str] = Field(default=None, description="mobile system info")
    mobile_model: Optional[str] = Field(default=None, description="mobile device model")
    mobile_brand: Optional[str] = Field(default=None, description="mobile device brand")
    module: Optional[str] = Field(default=None, description="module name")
    page: Optional[str] = Field(default=None, description="page name")
    event_name: Optional[str] = Field(default=None, description="event name")
    event_type: Optional[str] = Field(default=None, description="event type")
    report_source: Optional[str] = Field(default=None, description="report source")
    content_id: Optional[str] = Field(default=None, description="content uuid")
    position: Optional[str] = Field(default=None, description="position info")
    name: Optional[str] = Field(default=None, description="trigger component name")
    event_properties: Optional[dict] = Field(default=None, description="event properties")
    extra: Optional[dict] = Field(default=None, description="extra information")
    mp_scene: Optional[str] = Field(default=None, description="miniprogram scene")
    mp_version: Optional[str] = Field(default=None, description="miniprogram version")
    mp_platform: Optional[str] = Field(default=None, description="miniprogram platform")
    mp_sdk_version: Optional[str] = Field(default=None, description="miniprogram sdk version")
    mp_language: Optional[str] = Field(default=None, description="miniprogram language")

    model_config = ConfigDict(from_attributes=True)