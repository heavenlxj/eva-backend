from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SignRequest(BaseModel):

    app_id: str
    time_stamp: str
    nonce: str
    package: str


class NetworkConfig(BaseModel):
    wifiName: str
    password: str


class TokenData(BaseModel):
    user_id: str
