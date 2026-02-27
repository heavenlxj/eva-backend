#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WeCom (WeChat Work) related models and constants
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class WXWorkEventType:
    """WeCom callback event types"""
    ADD_EXTERNAL_CONTACT = "add_external_contact"
    DEL_EXTERNAL_CONTACT = "del_external_contact"
    DEL_FOLLOW_USER = "del_follow_user"


class WXWorkUser(BaseModel):
    """WeCom user info"""
    work_userid: str
    user_id: Optional[str] = None
    unionid: Optional[str] = None
    name: Optional[str] = None
    mobile: Optional[str] = None
    avatar: Optional[str] = None
    added_by: Optional[str] = None


class AddTagRequest(BaseModel):
    """Request to add tag to WeCom user"""
    child_id: str = Field(description="Child ID")
    add_tag: Optional[List[str]] = Field(default=None, description="(Deprecated)")
    remove_tag: Optional[List[str]] = Field(default=None, description="If provided, backend will remove the unified tag")


class AddTagResponse(BaseModel):
    """Response for adding tag to WeCom user"""
    child_id: str = Field(description="Child ID")
    external_userids: List[str] = Field(description="External user IDs that were processed")
    tags_added: List[str] = Field(description="Added tag IDs")
    tags_removed: Optional[List[str]] = Field(default=None, description="Removed tag IDs")
    message: str = Field(description="Result message")


class SendMiniprogramBatchResponse(BaseModel):
    """Response for batch sending miniprogram message and removing tags"""
    status: str = Field(description="Status: success, partial_success, failed")
    total_users: int = Field(description="Total users")
    success_count: int = Field(description="Success count")
    failed_count: int = Field(description="Failed count")
    tags_processed: List[str] = Field(description="Processed tag IDs")
    message: str = Field(description="Result message")


class SendMiniprogramByStaffRequest(BaseModel):
    """Request to send miniprogram message by all staff (auto iterate)"""
    tag_ids: List[str] = Field(description="Tag IDs")
    miniprogram_appid: Optional[str] = Field(default=None, description="Miniprogram APPID")
    miniprogram_page: str = Field(default="pages/index/index", description="Miniprogram page path")
    miniprogram_title: str = Field(default="Daily Push", description="Miniprogram message title")
    miniprogram_description: Optional[str] = Field(default="Click to view details", description="Miniprogram message description")
    thumb_media_id: Optional[str] = Field(default=None, description="Miniprogram cover image media_id")


# 自动回复内容
WXWORK_AUTO_REPLY_MESSAGE = (
    "如果您遇到产品使用问题，建议咨询购买平台的客服（如淘宝、京东、天猫）。\n"
    "他们会根据您的订单信息，为您提供最准确的解答和官方支持。"
)


# 欢迎语配置
# 注意：企业微信的 text 字段只能发送一条文本消息，多条文本需要合并
WELCOME_MESSAGE_TEXT = (
    "👋 亲爱的妈妈/爸爸，欢迎您和宝贝加入【可豆陪陪】大家庭！🎉\n\n"
    "🌟 可豆陪陪是谁？\n\n" 
    "它是您家宝贝的专属AI玩伴＋小老师！\n\n"
    "✅ 对孩子：通过趣味故事、互动游戏卡片，激发孩子的好奇心和表达能力，让宝贝在玩中学、学中玩～\n\n"
    "✅ 对您：懂您带娃的辛苦！它愿做您的\"省心帮手\"，分担陪伴压力，让您偶尔喘口气，轻松收获一个爱动脑、会表达的宝贝\n\n"
    "📈 专属福利提醒：\n\n"
    "成为好友后，我们还会不定期为您奉上宝贝的【成长洞察报告】，帮您发现孩子那些不经意间的创造力闪光点，一起见证成长每一步！\n\n"
    "为了方便快速为您开通专属1对1服务通道，辛苦提供一下购买的平台和订单号，我们会立刻安排哦！🤝"
)


WELCOME_MESSAGE_ATTACHMENTS = []

