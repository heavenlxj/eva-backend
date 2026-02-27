#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : settings.py

from typing import List
import json

from pydantic_settings import BaseSettings


class MySQLConfig(BaseSettings):

    HOST: str = "pc-2ze4j7g504317t961.rwlb.rds.aliyuncs.com"
    PORT: int = 3306
    USERNAME: str = "benepal_test"
    PASSWORD: str = "XOS3iePxHc+vud6z"
    DATABASE: str = "kido"
    ECHO: bool = False
    POOL_PRE_PING: bool = True
    POOL_SIZE: int = 50
    MAX_OVERFLOW: int = 200
    POOL_RECYCLE: int = 3600
    POOL_TIMEOUT: int = 30

    class Config:
        env_prefix = "KIDO_MYSQL_"


class StaticFileConfig(BaseSettings):

    DATA_DIR: str = "./data"
    IMAGES_DIR: str = "./data/images"
    IMAGE_BASE_URL: str = "/images"

    class Config:
        env_prefix = "STATIC_FILE_"


class RedisConfig(BaseSettings):

    HOST: str = "8.130.108.143"
    PORT: int = 6379
    PASSWORD: str = ""
    USER: str = "root"
    DB: int = 2
    URL: str = f"redis://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"

    class Config:
        env_prefix = "REDIS_"


class WeChat(BaseSettings):

    APPID: str = "wx269b622ec0a8fa09"
    SECRET: str = "a1f70a3e63da207284f9c59d6a81ba8e"
    SECRET_KEY: str = "36c69eaa3ec548e0af0165f37d1d6cb2"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 3000
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    SERVICE_APPID: str = "wx905fd3a22ac118a8"
    SERVICE_SECRET: str = "a7a64d7147a8d8e58e5e2466ab2b29b8"
    SERVICE_TOKEN: str = "BENEPAL"

    SECONDARY_APPID: str = "wx8ed40a98cf7d0f92"
    SECONDARY_SECRET: str = "6d008c643000f6d4f5ccce9d13ce61e8"
    
    # 切换开关：使用哪个小程序配置 (primary/secondary)
    USE_SECONDARY_APP: bool = False
    
    # 禁用微信内容安全验证
    DISABLE_WECHAT_CONTENT_SECURITY_CHECK: bool = True

    class Config:
        env_prefix = "WECHAT_"


class WeChatPayConfig(BaseSettings):
    """微信支付配置"""
    MCHID: str = "1697544418"  # 商户号
    PRIVATE_KEY_PATH: str = "./apiclient_key.pem"  # 商户证书私钥路径
    CERT_SERIAL_NO: str = "46997FE72D57FEF3EA34C6796DCBF44B88115F34"  # 商户证书序列号
    APIV3_KEY: str = "WDPZxxYGjQ77en6KXhS5po7n7igZpGjd"  # API v3密钥
    NOTIFY_URL: str = "https://benipally.com.cn/app/api/payment/wx-notify"  # 支付回调地址
    CERT_DIR: str = "./cert"  # 微信支付平台证书缓存目录
    PARTNER_MODE: bool = False  # 接入模式：False=直连商户模式，True=服务商模式
    PUBLIC_KEY_PATH: str = "./cert/pub_key.pem"  # 微信支付平台证书公钥路径
    PUBLICK_KEY_ID: str = "PUB_KEY_ID_0116975444182025123000182091002803"

    class Config:
        env_prefix = "WECHAT_PAY_"


class ExternalServiceConfig(BaseSettings):

    WHALE_URL: str = " http://127.0.0.1:8099"


class APISettings(BaseSettings):
    ENABLE_CLIENT_VERIFICATION: bool = False
    DISABLE_TOKEN_AUTH: bool = False

    class Config:
        env_prefix = "API_"


class RabbitMQConfig(BaseSettings):
    HOST: str = "8.130.108.143"
    PORT: int = 5672
    USERNAME: str = "benepal"
    PASSWORD: str = "999p*qm9bw4JQRxN_y6WZL"
    DATA_TRACKING_EXCHANGE: str = "data_tracking"
    DATA_TRACKING_QUEUE: str = "data_tracking_queue"
    USER_INTERACTION_QUEUE: str = "user_interaction_queue"

    class Config:
        env_prefix = "RABBITMQ_"


class RagConfig(BaseSettings):
    """RAG service configuration"""
    GRPC_HOST: str = "localhost"
    GRPC_PORT: int = 50051

    class Config:
        env_prefix = "RAG_"


class ServerConfig(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 9000
    LOG_LEVEL: str = "info"

    class Config:
        env_prefix = "SERVER_"


class ChildConfig(BaseSettings):
    WHITELIST_JSON: str = '["e262d7f1347a41669ae358588ea17b7d"]'  # 默认值
    
    @property
    def WHITELIST(self) -> List[str]:
        try:
            return json.loads(self.WHITELIST_JSON)
        except Exception:
            return []

    class Config:
        env_prefix = "KIDO_CHILD_"


class WXWorkConfig(BaseSettings):
    """WeCom config"""
    CORP_ID: str = "ww04f1f547dcdbaf73"
    AGENT_SECRET: str = "inF6JdKL7JYtqOHP_brKEfwbB11YDUdim__zfghdsuo"
    TOKEN: str = "D4LhJaKVGQxMg3DUiR7bxLoj"
    ENCODING_AES_KEY: str = "liFLvTXOV0BeKrXCoJ7ZCnD7tdz98UOCV2JY1Arf6vh"
    TASK_COMPLETED_TAG_ID: str = "et8wZWagAAsQKbtnhS7xhnQCFWKvce3g"
    TASK_COMPLETED_GROUP_ID: str = "et8wZWagAA85GPSmE3Vm9oCVxUt6nRGA"
    
    class Config:
        env_prefix = "WXWORK_"


class ShareConfig(BaseSettings):
    """分享功能配置"""
    INVITEE_UNLOCK_COUNT: int = 30  # 被分享人解锁数量
    SHARER_UNLOCK_COUNT: int = 30  # 分享人解锁数量
    BUCKET_NAME: str = "kidopally-app-test"  # 存储桶名称（测试环境）
    
    class Config:
        env_prefix = "SHARE_"


class DevConfig:
    static_file = StaticFileConfig()
    mysql = MySQLConfig()
    redis = RedisConfig()
    wechat = WeChat()
    wechat_pay = WeChatPayConfig()
    external = ExternalServiceConfig()
    api = APISettings()
    rabbitmq = RabbitMQConfig()
    server = ServerConfig()
    child = ChildConfig()
    rag = RagConfig()
    wxwork = WXWorkConfig()
    share = ShareConfig()