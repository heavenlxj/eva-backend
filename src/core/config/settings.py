from functools import lru_cache
import os
from .dev import DevConfig
from .prod import ProdConfig
from .test import TestConfig

@lru_cache
def get_settings():
    env = os.getenv("APP_ENV", "dev").lower()
    configs = {
        "dev": DevConfig,
        "test": TestConfig,
        "prod": ProdConfig,
    }
    config_class = configs.get(env, DevConfig)
    return config_class()

settings = get_settings()