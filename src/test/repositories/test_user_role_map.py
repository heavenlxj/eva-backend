#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : test_user_role_map.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_role_map import UserRoleMapRepository
from repositories.model.user_role_map import UserRoleMap
from repositories.model.user_role import UserRole


class TestUserRoleMapRepository:
    """UserRoleMapRepository 单元测试"""

    @pytest.fixture
    def mock_session(self):
        """创建模拟的 AsyncSession"""
        session = AsyncMock(spec=AsyncSession)
        
        # 创建一个异步上下文管理器工厂函数
        @asynccontextmanager
        async def mock_begin():
            yield None
        
        # 让 begin() 方法每次调用都返回一个新的异步上下文管理器
        def begin_factory():
            return mock_begin()
        
        session.begin = MagicMock(side_effect=begin_factory)
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """创建 UserRoleMapRepository 实例"""
        return UserRoleMapRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_user_roles_without_child_id(self, repository, mock_session):
        """测试获取用户角色（不指定 child_id）"""
        # 准备测试数据
        mock_role1 = UserRole(id=1, name="管理员", description="管理员角色")
        mock_role2 = UserRole(id=2, name="普通用户", description="普通用户角色")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_role1, mock_role2]
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await repository.get_user_roles("user123")
        
        # 验证结果
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        mock_session.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_roles_with_child_id(self, repository, mock_session):
        """测试获取用户角色（指定 child_id）"""
        # 准备测试数据
        mock_role = UserRole(id=3, name="家长", description="家长角色")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_role]
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await repository.get_user_roles("user123", "child456")
        
        # 验证结果
        assert len(result) == 1
        assert result[0].id == 3
        mock_session.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_user_role(self, repository, mock_session):
        """测试添加用户角色"""
        # 执行测试
        result = await repository.add_user_role("user123", 1)
        
        # 验证结果
        assert result.user_id == "user123"
        assert result.role_id == 1
        mock_session.add.assert_called_once()
        mock_session.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_user_role_exists(self, repository, mock_session):
        """测试移除存在的用户角色"""
        # 准备测试数据
        beijing_tz = timezone(timedelta(hours=8))
        mock_role_map = UserRoleMap(
            id=1,
            user_id="user123",
            child_id="child456",
            role_id=2,
            deleted_at=None
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_role_map
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        await repository.remove_user_role("user123", 2)
        
        # 验证结果
        assert mock_role_map.deleted_at is not None
        mock_session.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_user_role_not_exists(self, repository, mock_session):
        """测试移除不存在的用户角色"""
        # 准备测试数据
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        await repository.remove_user_role("user123", 2)
        
        # 验证结果（不应该抛出异常）
        mock_session.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_role_no_existing_roles(self, repository, mock_session):
        """测试更新用户角色 - 场景1: 没有现有角色，创建新角色"""
        # 准备测试数据
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        await repository.update_user_role("user123", 4, "child456")
        
        # 验证结果
        mock_session.add.assert_called_once()
        added_role_map = mock_session.add.call_args[0][0]
        assert added_role_map.user_id == "user123"
        assert added_role_map.child_id == "child456"
        assert added_role_map.role_id == 4
        assert added_role_map.deleted_at is None

    @pytest.mark.asyncio
    async def test_update_user_role_has_role_3_keep_it(self, repository, mock_session):
        """测试更新用户角色 - 场景2: 存在 role_id=3，保留它，清理其他记录"""
        # 准备测试数据
        beijing_tz = timezone(timedelta(hours=8))
        role_map_3 = UserRoleMap(
            id=1,
            user_id="user123",
            child_id="child456",
            role_id=3,
            deleted_at=None
        )
        role_map_4 = UserRoleMap(
            id=2,
            user_id="user123",
            child_id="child456",
            role_id=4,
            deleted_at=None
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [role_map_3, role_map_4]
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        await repository.update_user_role("user123", 4, "child456")
        
        # 验证结果
        # role_id=3 应该保留（deleted_at 为 None）
        assert role_map_3.deleted_at is None
        # role_id=4 应该被标记为删除
        assert role_map_4.deleted_at is not None
        # 不应该创建新记录
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_role_has_role_3_only(self, repository, mock_session):
        """测试更新用户角色 - 场景2变体: 只有 role_id=3，应该保留"""
        # 准备测试数据
        role_map_3 = UserRoleMap(
            id=1,
            user_id="user123",
            child_id="child456",
            role_id=3,
            deleted_at=None
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [role_map_3]
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        await repository.update_user_role("user123", 4, "child456")
        
        # 验证结果
        # role_id=3 应该保留
        assert role_map_3.deleted_at is None
        # 不应该创建新记录
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_role_no_role_3_clean_all(self, repository, mock_session):
        """测试更新用户角色 - 场景3: 没有 role_id=3，清理所有记录并创建新记录"""
        # 准备测试数据
        role_map_4 = UserRoleMap(
            id=1,
            user_id="user123",
            child_id="child456",
            role_id=4,
            deleted_at=None
        )
        role_map_5 = UserRoleMap(
            id=2,
            user_id="user123",
            child_id="child456",
            role_id=5,
            deleted_at=None
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [role_map_4, role_map_5]
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        await repository.update_user_role("user123", 6, "child456")
        
        # 验证结果
        # 所有旧记录应该被标记为删除
        assert role_map_4.deleted_at is not None
        assert role_map_5.deleted_at is not None
        # 应该创建新记录
        mock_session.add.assert_called_once()
        added_role_map = mock_session.add.call_args[0][0]
        assert added_role_map.user_id == "user123"
        assert added_role_map.child_id == "child456"
        assert added_role_map.role_id == 6
        assert added_role_map.deleted_at is None

    @pytest.mark.asyncio
    async def test_update_user_role_no_role_3_single_record(self, repository, mock_session):
        """测试更新用户角色 - 场景3变体: 只有一条非 role_id=3 的记录"""
        # 准备测试数据
        role_map_4 = UserRoleMap(
            id=1,
            user_id="user123",
            child_id="child456",
            role_id=4,
            deleted_at=None
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [role_map_4]
        
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        await repository.update_user_role("user123", 5, "child456")
        
        # 验证结果
        # 旧记录应该被标记为删除
        assert role_map_4.deleted_at is not None
        # 应该创建新记录
        mock_session.add.assert_called_once()
        added_role_map = mock_session.add.call_args[0][0]
        assert added_role_map.role_id == 5

