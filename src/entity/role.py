from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class RoleInfo(BaseModel):
    role_id: str = Field(description="角色唯一标识")
    name: str = Field(description="角色名称")
    nick_name: Optional[str] = Field(description="角色昵称", default=None)
    gender: Optional[str] = Field(description="性别", default=None)
    description: Optional[str] = Field(description="角色描述", default=None)
    personality_traits: Optional[Dict[str, Any]] = Field(description="性格特征", default=None)
    tone_style: Optional[str] = Field(description="说话风格", default=None)
    background_story: Optional[str] = Field(description="背景故事", default=None)
    avatar_url: Optional[str] = Field(description="头像 URL", default=None)
    language: str = Field(description="语言", default="zh-CN")

    model_config = ConfigDict(from_attributes=True)


class BindRoleRequest(BaseModel):
    role_id: str = Field(description="角色ID")


class UserRoleBindingInfo(BaseModel):
    role_id: str = Field(description="角色ID")
    role_name: Optional[str] = Field(description="角色名称", default=None)
    nick_name: Optional[str] = Field(description="角色昵称", default=None)
    created_at: Optional[datetime] = Field(description="绑定时间", default=None)

    model_config = ConfigDict(from_attributes=True)
