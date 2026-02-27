
from loguru import logger
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, Optional

from entity.login import TokenData
from core.config.settings import settings

# SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
SECRET_KEY = "36c69eaa3ec548e0af0165f37d1d6cb2"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(data: dict):
    """生成Access Token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    """生成Refresh Token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"payload: {payload}")
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not logged in or Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(user_id=user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def refresh_token(
        token: HTTPAuthorizationCredentials | None):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in or Invalid credentials",
        )
    token_data = decode_token(token.credentials)
    access_token = create_access_token({"user_id": token_data.user_id})
    return {"access_token": access_token}

async def analysis_from_token(
    token: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
) -> Optional[TokenData]:
    if settings.api.DISABLE_TOKEN_AUTH:
        logger.warning("Token authentication is disabled for local testing")
        return TokenData(user_id="00000000000000000000000000000000")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in or Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(token.credentials)

AuthUser = Annotated[TokenData, Depends(analysis_from_token)]
#
# if __name__ == '__main__':
#     import asyncio
#     token = asyncio.run(create_access_token("073d0b47cb7a4bcdb800fe2d1cebebf3"))
#     print(token)