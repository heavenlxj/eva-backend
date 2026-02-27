from typing import Optional
from pydantic import BaseModel, Field
from core.config.settings import settings

BUSINESS_COOPERATION = "BUSINESS_COOPERATION"

class WechatMiniLink:

    @staticmethod
    def get_menu_config():
        """获取菜单配置，使用当前配置的APPID"""
        # 获取当前配置的APPID
        if settings.wechat.USE_SECONDARY_APP:
            current_appid = settings.wechat.SECONDARY_APPID
        else:
            current_appid = settings.wechat.APPID
        
        return {
            "button": [
                {
                    "name": "常用功能",
                    "sub_button": [
                        {
                            "type": "miniprogram",
                            "name": "家长端小程序",
                            "url": "https://kidopally.cn",
                            "appid": current_appid,
                            "pagepath": "/pages/loading/loading"
                        },
                        {
                            "type": "miniprogram",
                            "name": "快速上手视频",
                            "url": "https://kidopally.cn",
                            "appid": current_appid,
                            "pagepath": "/pages/profile_pages/video/video"
                        },
                        {
                            "type": "view",
                            "name": "产品使用手册",
                            "url": "https://kidopally.cn/zh/manual"
                        },
                        {
                            "type": "view",
                            "name": "官方视频",
                            "url": "https://weixin.qq.com/sph/A6XXtWWaT"
                        }
                    ]
                },
                {
                    "type": "view",
                    "name": "晒单有礼",
                    "url": "https://mp.weixin.qq.com/s/-dNIpdrUoUDWqsAidNClig"
                },
                {
                    "name": "联系我们",
                    "sub_button": [
                        {
                            "type": "click",
                            "name": "商务合作",
                            "key": BUSINESS_COOPERATION
                        },
                        {
                            "type": "miniprogram",
                            "name": "意见与建议",
                            "url": "https://kidopally.cn",
                            "appid": current_appid,
                            "pagepath": "pages/profile_pages/feedback/feedback"
                        }
                    ]
                }
            ]
        }
    
    # 保持向后兼容，但使用动态方法
    MENU_CONFIG = get_menu_config()
    FIRST_MINI_LINK = [
        {
            'desc': '👉🏻新用户常用操作\n',
            'path': '/pages/loading/loading',
            'query': 'from=notification&page=/pages/loading/loading',
            'url_text': '首次使用快速联网'
        },
        {
            'desc': '',
            'path': '/pages/profile_pages/video/video',
            'query': 'from=notification&page=/pages/profile_pages/video/video',
            'url_text': '快速上手教学视频'
        },
        {
            'desc': '',
            'path': 'pages/content/content_library/content_library',
            'query': 'from=notification&page=pages/content/content_library/content_library',
            'url_text': '功能和内容大全'
        },
        {
            'desc': '👉🏻老用户常用操作\n',
            'path': '/pages/loading/loading',
            'query': 'from=notification&page=pages/guide/wifi_config/wifi_config',
            'url_text': '重新配置网络'
        },
        {
            'desc': '',
            'path': '/pages/loading/loading',
            'query': 'from=notification&page=/pages/loading/loading',
            'url_text': '进入小程序'
        }
    ]
    AUTO_REPLY_CONFIG = [
        {
            "key": BUSINESS_COOPERATION,
            "type": "text",
            "content": "您好！感谢关注【可豆陪陪】❤️\n如需协助或合作，请通过邮箱与我们联系：\n📧 marketing@benepal.com\n✨我们将尽快回复您的邮件哦！"
        }
    ]
    
    # 通用自动回复配置
    GENERAL_AUTO_REPLY = "如果您遇到产品使用问题，建议咨询购买平台的客服（如淘宝、京东、天猫）。他们会根据您的订单信息，为您提供最准确的解答和官方支持。"



class WechatErrorCode:
    """WeChat error codes"""
    USER_REFUSE_MESSAGE = 43101
    RATE_LIMIT_SECOND_LEVEL = 40258  # 二级限流：短时间内向同一用户发送相同内容
    REQUIRE_SUBSCRIBE = 43004  # 需要用户关注公众号才能接收模板消息


class ContentSecurityScene:
    """Content security check scene enum"""
    PROFILE = 1
    COMMENT = 2
    FORUM = 3
    SOCIAL_LOG = 4


class ContentSecurityLabel:
    """Content security label enum"""
    NORMAL = 100
    AD = 10001
    POLITICS = 20001
    PORN = 20002
    ABUSE = 20003
    ILLEGAL = 20006
    FRAUD = 20008
    VULGAR = 20012
    COPYRIGHT = 20013
    OTHER = 21000


class ContentSecuritySuggest:
    """Content security suggestion enum"""
    PASS = "pass"
    REVIEW = "review"
    RISKY = "risky"


class ContentSecurityCheckRequest(BaseModel):
    """Content security check request model"""
    content: str = Field(..., description="Content to check (max 2500 chars)", max_length=2500)
    scene: int = Field(default=ContentSecurityScene.COMMENT, description="Scene: 1=profile 2=comment 3=forum 4=social")
    title: Optional[str] = Field(default=None, description="Title (optional)")
    nickname: Optional[str] = Field(default=None, description="Nickname (optional)")
    signature: Optional[str] = Field(default=None, description="Signature (optional, profile scene only)")


class WechatContentSecurityResult(BaseModel):
    """微信内容安全检查结果"""
    safe: bool = Field(..., description="是否安全")
    suggest: str = Field(..., description="建议：pass/review/risky")
    label: int = Field(..., description="标签代码")
    detail: list = Field(default=[], description="详细信息")
    trace_id: str = Field(default="", description="追踪ID")