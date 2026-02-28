from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


class UserLoginRequest(BaseModel):

    code: Optional[str] = Field(description='wx login session code')
    source: Optional[str] = Field(description='indicate user login source, e.g. mini_program, wx')
    app_id: Optional[str] = Field(description='app id', default=None)


class UserLoginResponse(BaseModel):

    user_id: str | None = Field(description='user id')
    access_token: Optional[str] = Field(description='access token')
    refresh_token: Optional[str] = Field(description='refresh token')
    experiments: Optional[Dict[str, "ExperimentAssignment"]] = Field(
        default=None,
        description="登录命中实验分桶信息"
    )

class UserInfo(BaseModel):
    id: int | None = None
    user_id: str | None = None
    nickname: str | None = None
    gender: str | None = None
    avatar_url: str | None = None
    birthday: str | None = None
    phone: str | None = None
    email: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class CreateUserRequest(BaseModel):
    nickname: str | None = Field(description="nick name", default=None)
    birthday: str | None = Field(description="birthday", default=None)
    gender: str | None = Field(description="gender", default=None)
    avatar_url: str | None = Field(description="avatar url", default=None)
    phone: str | None = Field(description="phone number", default= None)
    email: str | None = Field(description="email", default=None)


class UpdateUserRequest(CreateUserRequest):
    ...


class BindDeviceRequest(BaseModel):
    device_id: str = Field(description="设备ID")


class UnbindDeviceRequest(BaseModel):
    device_id: str = Field(description="设备ID")


# Template message related data structures
class MiniprogramInfo(BaseModel):
    """Miniprogram jump information"""
    appid: str = Field(description="miniprogram appid")
    pagepath: str = Field(description="miniprogram page path, e.g.: pages/index/index")


class TemplateDataItem(BaseModel):
    """Template data item - directly corresponds to WeChat API format"""
    value: str = Field(description="data value")
class SendTemplateMessageRequest(BaseModel):
    """Send template message request"""
    service_openid: str = Field(description="recipient openid")
    template_id: str = Field(description="template ID")
    data: Dict[str, TemplateDataItem] = Field(description="template data, parameter names correspond to template configuration")
    url: Optional[str] = Field(description="click to jump to web page link", default=None)
    miniprogram: Optional[MiniprogramInfo] = Field(description="jump to miniprogram information", default=None)


class SendTemplateMessageByUserRequest(BaseModel):
    """Send template message via user_id request"""
    user_id: str = Field(description="user ID")
    template_id: str = Field(description="template ID")
    data: Dict[str, TemplateDataItem] = Field(description="template data, parameter names correspond to template configuration")
    url: Optional[str] = Field(description="click to jump to web page link", default=None)
    miniprogram: Optional[MiniprogramInfo] = Field(description="jump to miniprogram information", default=None)


class SendTemplateMessageByChildRequest(BaseModel):
    """Send template message via child_id request"""
    child_id: str = Field(description="child ID")
    template_id: str = Field(description="template ID")
    data: Dict[str, TemplateDataItem] = Field(description="template data, parameter names correspond to template configuration")
    url: Optional[str] = Field(description="click to jump to web page link", default=None)
    miniprogram: Optional[MiniprogramInfo] = Field(description="jump to miniprogram information", default=None)


class TemplateMessageResponse(BaseModel):
    """Template message response"""
    code: int = Field(description="response code, 0 means success")
    message: str = Field(description="response message")
    data: Optional[Dict[str, Any]] = Field(description="response data", default=None)


class ExperimentAssignment(BaseModel):
    bucket: str = Field(description="实验分桶名称")
    description: Optional[str] = Field(description="桶描述", default=None)


UserLoginResponse.model_rebuild()