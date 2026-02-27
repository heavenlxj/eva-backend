import uuid
from loguru import logger
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from entity.login import TokenData
from entity.user import (
    UpdateUserRequest,
    UserInfo,
    UserLoginRequest,
    CreateUserRequest,
    UserLoginResponse,
    ExperimentAssignment,
)

from repositories.user import UserRepository

from repositories.user_source import UserSourceRepository
from repositories.userid_unionid_mapping import UseridUnionidMappingRepository
from repositories.miniprogram_config import MiniprogramConfigRepository
from services.weixin import WechatService
from auth import create_access_token, create_refresh_token


class UserService:

    def __init__(self, db: AsyncSession, token: TokenData=None):
        self.db = db
        self.token = token
        self.user_repo = UserRepository(db)
        self.user_resource_repo = UserSourceRepository(db)
        self.userid_unionid_mapping_repo = UseridUnionidMappingRepository(db)
        miniprogram_repo = MiniprogramConfigRepository(db)

    async def get_user(self) -> Optional[UserInfo]:
        user_info = await self.user_repo.get(user_id=self.token.user_id)
        if user_info is None:
            return None

        return UserInfo.model_validate(user_info)

    async def user_login(self, login_request: UserLoginRequest) -> Optional[UserLoginResponse]:
        user_info = await WechatService.get_user_info_with_unionid(login_request.code, login_request.app_id)
        logger.info(f"user_info: {user_info}")
        
        if not user_info or not user_info.get('openid'):
            return None

        user = await self.get_or_create_user_by_openid_with_unionid(
            user_info.get('openid'), 
            user_info.get('unionid'), 
            login_request.source
        )
        if user is None:
            return None
        
        await self.user_visit_repo.record_visit(user.user_id)
        logger.info(f"user {user.user_id} visit stats recorded")

        access_token = create_access_token({"user_id": user.user_id})
        refresh_token = create_refresh_token({"user_id": user.user_id})

        experiments = await self.experiments_service.assign(user.user_id)

        login_resp = UserLoginResponse(
            user_id=user.user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            experiments=experiments,
        )

        return login_resp



    async def get_or_create_user_by_openid(self, openid: str, source: str) -> UserInfo | None:
        try:
            user_source = await self.user_resource_repo.get_with_open_id(openid=openid, source=source)
            logger.info(f"user_source: {user_source}")
            if user_source:
                user = await self.user_repo.get(user_id=user_source.user_id)
                logger.info(f"找到 user: {user}")
            else:
                user_id = uuid.uuid4().hex
                user = await self.user_repo.create(user_id=user_id)
                await self.user_resource_repo.create(user_id=user_id, openid=openid, source=source)
                logger.info(f"创建新用户: {user_id}")
            
            beijing_tz = timezone(timedelta(hours=8))
            return UserInfo(
                user_id=user.user_id,
                created_at=datetime.now(beijing_tz),
                updated_at=datetime.now(beijing_tz)
            )
        except NoResultFound:
            return None

    async def get_or_create_user_by_openid_with_unionid(self, openid: str, unionid: str, source: str) -> UserInfo | None:
        """通过openid和unionid获取或创建用户，实现数据迁移逻辑"""
        try:
            # 在外层开启一个事务，确保所有操作在同一个事务中
            async with self.db.begin():
                # 0. 优先从userid_unionid_mapping表根据unionid获取user_id
                if unionid:
                    mapping = await self.userid_unionid_mapping_repo.get_by_unionid(unionid)
                    logger.info(f"通过unionid查询userid_unionid_mapping结果: {mapping}")
                    
                    if mapping:
                        # 如果找到映射关系，直接获取用户信息并返回
                        user = await self.user_repo.get(user_id=mapping.user_id)
                        logger.info(f"通过userid_unionid_mapping找到现有用户: {user}")
                        
                        beijing_tz = timezone(timedelta(hours=8))
                        return UserInfo(
                            user_id=user.user_id,
                            created_at=datetime.now(beijing_tz),
                            updated_at=datetime.now(beijing_tz)
                        )
                
                # 1. 如果没有找到映射关系，先用unionid查询user_source表
                user_source = None
                if unionid:
                    user_source = await self.user_resource_repo.get_by_unionid(unionid=unionid, source=source)
                    logger.info(f"通过unionid查询user_source结果: {user_source}")
                
                if user_source:
                    # 如果通过unionid找到记录，获取userid并更新userid_unionid_mapping
                    user = await self.user_repo.get(user_id=user_source.user_id)
                    logger.info(f"通过unionid找到现有用户: {user}")
                    
                    # 插入或更新userid_unionid_mapping表
                    await self._ensure_userid_unionid_mapping(user.user_id, unionid)
                    
                else:
                    # 2. 如果没有unionid记录，再用openid查询
                    user_source = await self.user_resource_repo.get_with_open_id(openid=openid, source=source)
                    logger.info(f"通过openid查询user_source结果: {user_source}")
                    
                    if user_source:
                        # 如果通过openid找到记录，更新unionid和添加mapping
                        user = await self.user_repo.get(user_id=user_source.user_id)
                        logger.info(f"通过openid找到现有用户: {user}")
                        
                        # 更新user_source表中的unionid（如果之前没有）
                        if unionid and not user_source.union_id:
                            await self.user_resource_repo.update_unionid(user_source.id, unionid)
                            logger.info(f"更新user_source表中的unionid: {unionid}")
                        
                        # 插入或更新userid_unionid_mapping表
                        await self._ensure_userid_unionid_mapping(user.user_id, unionid)
                        
                    else:
                        # 3. 如果用openid也查不到记录，创建新用户
                        user_id = uuid.uuid4().hex
                        user = await self.user_repo.create(user_id=user_id)
                        logger.info(f"创建新用户: {user_id}")
                        
                        # 插入user_source表记录
                        await self.user_resource_repo.create(
                            user_id=user_id, 
                            openid=openid, 
                            source=source,
                            unionid=unionid
                        )
                        logger.info(f"插入user_source表记录: user_id={user_id}, openid={openid}, unionid={unionid}")
                        
                        # 插入userid_unionid_mapping表
                        if unionid:
                            await self._ensure_userid_unionid_mapping(user_id, unionid)
                
                beijing_tz = timezone(timedelta(hours=8))
                return UserInfo(
                    user_id=user.user_id,
                    created_at=datetime.now(beijing_tz),
                    updated_at=datetime.now(beijing_tz)
                )
        except NoResultFound:
            return None

    async def _ensure_userid_unionid_mapping(self, user_id: str, unionid: str) -> None:
        """确保userid_unionid_mapping表中存在映射关系"""
        if not unionid:
            logger.info(f"UnionID为空，跳过映射表操作: user_id={user_id}")
            return
            
        try:
            # 检查是否已存在映射关系
            existing_mapping = await self.userid_unionid_mapping_repo.get_by_user_id(user_id)
            
            if existing_mapping:
                # 如果存在但unionid不同，则更新
                if existing_mapping.unionid != unionid:
                    await self.userid_unionid_mapping_repo.update_unionid(user_id, unionid)
                    logger.info(f"更新userid_unionid_mapping: user_id={user_id}, unionid={unionid}")
                else:
                    logger.info(f"userid_unionid_mapping已存在且相同: user_id={user_id}, unionid={unionid}")
            else:
                # 如果不存在，则创建新的映射关系
                await self.userid_unionid_mapping_repo.create(user_id, unionid)
                logger.info(f"创建新的userid_unionid_mapping: user_id={user_id}, unionid={unionid}")
                
        except Exception as e:
            logger.error(f"处理userid_unionid_mapping时出错: {e}")

    async def update_user(self, user_info: UpdateUserRequest) -> UserInfo:
        user = await self.user_repo.update(self.token.user_id, user_info)
        return UserInfo.model_validate(user)


class InternalUserService:

    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def create_user(self, user_info: CreateUserRequest) -> None:
        user_id = uuid.uuid4().hex
        _ = await self.user_repo.create(
            user_id=user_id,
            phone=user_info.phone,
            nickname=user_info.nickname,
            avatar_url=user_info.avatar_url,
            birthday=user_info.birthday,
            email=user_info.email,
        )
        return
