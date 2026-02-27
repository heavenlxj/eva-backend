# 小程序分享裂变功能设计文档

## 一、功能概述

实现小程序内容分享裂变功能，通过分享漫画/海报二维码，引导新用户注册并绑定设备，给予分享人奖励（解锁诗词进度）。

## 二、核心流程

### 2.1 分享流程

```
用户A点击分享
  ↓
生成分享链接/二维码（携带 sharer_user_id=A）
  ↓
用户B扫码进入小程序（携带 sharer_user_id=A）
  ↓
小程序解析参数，记录分享关系（状态：未激活）
  ↓
用户B完成配网绑定设备
  ↓
触发激活检查（检查是否有 sharer_user_id）
  ↓
激活成功，给用户A解锁奖励（+10首）
  ↓
更新分享关系状态为：已激活
```

### 2.2 前后端联动流程

#### 前端流程

**1. 分享生成阶段**
- 用户点击"分享漫画"或"分享海报"
- 调用后端接口生成分享码（包含 sharer_user_id）
- 生成二维码（小程序码），携带参数：`sharer_user_id={当前用户ID}`
- 用户保存/分享二维码

**2. 扫码进入阶段**
- 新用户B扫描二维码进入小程序
- 小程序 `onLoad` 接收参数：`sharer_user_id=A`
- 调用后端接口记录分享关系（`POST /api/share/record`）
- 将 `sharer_user_id` 存储到本地 `userStorage`

**3. 配网绑定阶段**
- 用户B完成配网流程（`wifi_connect` 页面）
- 设备绑定成功后，检查本地是否有 `sharer_user_id`
- 如果有，调用激活接口（`POST /api/share/activate`）
- 后端验证并激活分享关系，给分享人解锁奖励

#### 后端流程

**1. 记录分享关系**
- 接收前端请求：`sharer_user_id`, `invitee_user_id`（当前用户）
- 检查是否已存在该分享关系（避免重复）
- 创建分享记录，状态：`pending`（待激活）

**2. 激活分享关系**
- 接收激活请求：`invitee_user_id`, `device_id`
- 验证：用户是否已绑定设备
- 查找待激活的分享记录（`sharer_user_id` 对应的 `pending` 记录）
- 更新记录状态为 `activated`
- 给分享人解锁奖励（增加解锁进度）
- 记录奖励发放日志

## 三、数据库表结构

### 3.1 分享关系表 `user_share_records`

```sql
CREATE TABLE `user_share_records` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `sharer_user_id` varchar(32) NOT NULL COMMENT '分享人用户ID',
  `invitee_user_id` varchar(32) NOT NULL COMMENT '被邀请人用户ID',
  `status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT '状态：pending(待激活)/activated(已激活)/expired(已过期)',
  `share_type` varchar(20) DEFAULT NULL COMMENT '分享类型：comic(漫画)/poster(海报)',
  `device_id` varchar(64) DEFAULT NULL COMMENT '激活时绑定的设备ID',
  `activated_at` timestamp NULL DEFAULT NULL COMMENT '激活时间',
  `reward_unlocked_count` int(11) DEFAULT 0 COMMENT '解锁的诗词数量（增量）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间（软删除）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sharer_invitee` (`sharer_user_id`, `invitee_user_id`, `deleted_at`),
  KEY `idx_sharer_user_id` (`sharer_user_id`),
  KEY `idx_invitee_user_id` (`invitee_user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户分享关系表';
```

### 3.2 用户解锁进度表 `user_unlock_progress`

```sql
CREATE TABLE `user_unlock_progress` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` varchar(32) NOT NULL COMMENT '用户ID',
  `total_unlocked_count` int(11) NOT NULL DEFAULT 0 COMMENT '总解锁数量（累计）',
  `total_poems_count` int(11) NOT NULL DEFAULT 300 COMMENT '总诗词数量（固定值）',
  `last_unlocked_at` timestamp NULL DEFAULT NULL COMMENT '最后解锁时间',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间（软删除）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_id` (`user_id`, `deleted_at`),
  KEY `idx_total_unlocked_count` (`total_unlocked_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户解锁进度表';
```

### 3.3 诗词表 `poems`

```sql
CREATE TABLE `poems` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `resource_id` varchar(255) NOT NULL COMMENT '资源ID',
  `title` varchar(255) NOT NULL COMMENT '标题',
  `content` text NOT NULL COMMENT '内容',
  `author` varchar(255) NOT NULL COMMENT '作者',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间（软删除）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `resource_id` (`resource_id`),
  UNIQUE KEY `unq_author_title` (`author`,`title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='诗词表';
```

## 四、后端接口文档

### 4.1 记录分享关系

**接口：** `POST /api/share/record`

**请求参数：**
```json
{
  "sharer_user_id": "user_123",  // 分享人用户ID（从二维码参数获取）
  "share_type": "comic"           // 分享类型：comic/poster
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "share_record_id": 1,
    "status": "pending"
  }
}
```

**业务逻辑：**
1. 从请求头获取当前用户ID（`invitee_user_id`）
2. 检查是否已存在相同的分享关系（避免重复记录）
3. 创建分享记录，状态为 `pending`
4. 返回记录ID

**错误处理：**
- `sharer_user_id` 不能等于当前用户ID（不能自己邀请自己）
- 已存在相同的分享关系，返回已存在的记录

### 4.2 激活分享关系

**接口：** `POST /api/share/activate`

**请求参数：**
```json
{
  "device_id": "device_123"  // 可选，用于记录激活时绑定的设备
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "activated": true,
    "share_record_id": 1,
    "reward_unlocked_count": 10,
    "sharer_user_id": "user_123"
  }
}
```

**业务逻辑：**
1. 从请求头获取当前用户ID（`invitee_user_id`）
2. 验证用户是否已绑定设备（通过 `device_id` 或查询用户设备绑定关系）
3. 查找该用户的所有 `pending` 状态的分享记录
4. 遍历分享记录，激活每个有效的分享关系：
   - 更新记录状态为 `activated`
   - 记录 `device_id` 和 `activated_at`
   - 给对应的 `sharer_user_id` 解锁奖励
5. 返回激活结果

**解锁奖励逻辑：**
1. 使用常量配置：`SHARE_ACTIVATE_REWARD = 10`（成功激活一个分享关系解锁的诗词数量）
2. 查询或创建用户的解锁进度记录
3. 更新 `total_unlocked_count`（增加奖励数量）

**错误处理：**
- 用户未绑定设备，返回错误
- 没有待激活的分享记录，返回 `activated: false`

### 4.3 获取我的邀请记录

**接口：** `GET /api/share/my-invites`

**请求参数：**
- 无（从请求头获取当前用户ID）

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_count": 2,
    "activated_count": 1,
    "pending_count": 1,
    "invites": [
      {
        "share_record_id": 1,
        "invitee_user_id": "user_B",
        "invitee_nickname": "用户B",
        "invitee_avatar": "https://...",
        "status": "activated",
        "activated_at": "2024-01-15 10:30:00",
        "reward_unlocked_count": 10,
        "created_at": "2024-01-10 09:00:00"
      },
      {
        "share_record_id": 2,
        "invitee_user_id": "user_D",
        "invitee_nickname": "用户D",
        "invitee_avatar": "https://...",
        "status": "pending",
        "activated_at": null,
        "reward_unlocked_count": 0,
        "created_at": "2024-01-12 14:20:00"
      }
    ]
  }
}
```

**业务逻辑：**
1. 从请求头获取当前用户ID（`sharer_user_id`）
2. 查询该用户的所有分享记录（`sharer_user_id = 当前用户ID`）
3. 关联查询被邀请人的基本信息（昵称、头像等）
4. 统计已激活和待激活数量
5. 返回列表数据

### 4.4 获取我的邀请人

**接口：** `GET /api/share/my-inviters`

**请求参数：**
- 无（从请求头获取当前用户ID）

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_count": 2,
    "inviters": [
      {
        "share_record_id": 1,
        "sharer_user_id": "user_A",
        "sharer_nickname": "用户A",
        "sharer_avatar": "https://...",
        "status": "activated",
        "activated_at": "2024-01-15 10:30:00",
        "created_at": "2024-01-10 09:00:00"
      },
      {
        "share_record_id": 3,
        "sharer_user_id": "user_C",
        "sharer_nickname": "用户C",
        "sharer_avatar": "https://...",
        "status": "activated",
        "activated_at": "2024-01-16 11:00:00",
        "created_at": "2024-01-11 08:15:00"
      }
    ]
  }
}
```

**业务逻辑：**
1. 从请求头获取当前用户ID（`invitee_user_id`）
2. 查询该用户的所有分享记录（`invitee_user_id = 当前用户ID`）
3. 关联查询邀请人的基本信息（昵称、头像等）
4. 返回列表数据

### 4.5 获取我的解锁进度

**接口：** `GET /api/share/unlock-progress`

**请求参数：**
- 无（从请求头获取当前用户ID）

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": "user_123",
    "total_unlocked_count": 20,
    "total_poems_count": 300,
    "unlocked_poem_numbers": [1, 2, 3, ..., 20],  // 已解锁的诗词编号列表（从1开始）
    "last_unlocked_at": "2024-01-15 10:30:00"
  }
}
```

**业务逻辑：**
1. 从请求头获取当前用户ID
2. 查询用户的解锁进度记录
3. 如果不存在，创建默认记录（`total_unlocked_count=0`）
4. 生成已解锁的诗词编号列表（从1开始，按顺序）
5. 返回进度数据

### 4.6 生成分享码（小程序码）

**接口：** `POST /api/share/generate-code`

**请求参数：**
```json
{
  "share_type": "comic",  // 分享类型：comic/poster
  "page": "pages/comic/comic",  // 小程序页面路径
  "scene": "share_comic"  // 场景值标识
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "qr_code_url": "https://...",  // 小程序码图片URL
    "share_path": "pages/comic/comic?sharer_user_id=user_123"  // 分享路径
  }
}
```

**业务逻辑：**
1. 从请求头获取当前用户ID（`sharer_user_id`）
2. 调用微信小程序码生成接口（`wxacode.getUnlimited`）
3. 生成分享路径，携带参数：`sharer_user_id={当前用户ID}`
4. 上传小程序码图片到OSS/CDN
5. 返回图片URL和分享路径

### 4.7 获取诗词列表（分页）

**接口：** `GET /api/share/poems`

**请求参数：**
- `author` (可选): 作者，精确匹配
- `title` (可选): 标题，支持模糊搜索
- `sort_by` (可选): 排序字段，默认 `created_at`，可选字段：`id`, `title`, `author`, `created_at`, `updated_at`
- `order` (可选): 排序方向，默认 `desc`，可选值：`asc`（升序）/ `desc`（降序）
- `page` (可选): 页码，默认 `1`，最小值为 `1`
- `page_size` (可选): 每页大小，默认 `50`，范围：`1-200`

**请求示例：**
```
GET /api/share/poems?author=李白&title=静夜&page=1&page_size=20&sort_by=created_at&order=desc
```

**响应：**
```json
{
  "code": 0,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 1,
        "resource_id": "poem_001",
        "title": "静夜思",
        "content": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
        "author": "李白",
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:30:00"
      },
      {
        "id": 2,
        "resource_id": "poem_002",
        "title": "望庐山瀑布",
        "content": "日照香炉生紫烟，遥看瀑布挂前川。飞流直下三千尺，疑是银河落九天。",
        "author": "李白",
        "created_at": "2024-01-15T10:31:00",
        "updated_at": "2024-01-15T10:31:00"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

**业务逻辑：**
1. 从请求头获取当前用户ID（用于日志记录）
2. 根据查询参数构建查询条件：
   - 如果提供 `author`，按作者精确匹配
   - 如果提供 `title`，按标题模糊搜索（使用 `LIKE`）
   - 过滤已删除的记录（`deleted_at IS NULL`）
3. 根据 `sort_by` 和 `order` 参数进行排序，默认按创建时间倒序
4. 使用分页参数进行分页查询
5. 返回分页结果

**错误处理：**
- 查询异常时返回错误信息，`code` 为 `-1`
- 错误时返回空列表，`total` 为 `0`

**使用场景：**
- 用户浏览已解锁的诗词列表
- 根据作者或标题搜索诗词
- 支持分页加载，提升性能

## 五、前端实现要点

### 5.1 分享参数传递

**分享漫画页面（`pages/comic/comic.ts`）**

```typescript
// 分享时生成小程序码
onShareAppMessage() {
  const currentUser = userStorage.getCurrentUser();
  return {
    title: '分享漫画',
    path: `pages/comic/comic?sharer_user_id=${currentUser.user_id}`,
    imageUrl: '...'
  };
}

// 页面加载时解析参数
async onLoad(options: any) {
  // 解析分享参数
  if (options.sharer_user_id) {
    const sharerUserId = options.sharer_user_id;
    // 记录分享关系
    await ShareService.recordShare({
      sharer_user_id: sharerUserId,
      share_type: 'comic'
    });
    // 存储到本地，用于后续激活
    userStorage.setSharerUserId(sharerUserId);
  }
}
```

### 5.2 激活时机

**配网绑定成功时（`pages/guide/wifi_connect/wifi_connect.ts`）**

```typescript
// 在设备绑定成功后，检查并激活分享关系
async registerDevice() {
  if (this.data.isFirstSetup) {
    // ... 设备注册逻辑 ...
    
    // 检查是否有分享人信息
    const sharerUserId = userStorage.getSharerUserId();
    if (sharerUserId) {
      try {
        // 激活分享关系
        const result = await ShareService.activateShare({
          device_id: deviceId
        });
        
        if (result.activated) {
          wx.showToast({
            title: '分享激活成功',
            icon: 'success'
          });
          // 清除本地存储的分享人信息
          userStorage.clearSharerUserId();
        }
      } catch (error) {
        console.error('激活分享关系失败:', error);
      }
    }
  }
}
```

### 5.3 获取诗词列表

**诗词列表页面（`pages/poem/list.ts`）**

```typescript
// 获取诗词列表
async loadPoems() {
  try {
    const params = {
      page: this.data.currentPage,
      page_size: 20,
      sort_by: 'created_at',
      order: 'desc'
    };
    
    // 如果有搜索条件
    if (this.data.searchAuthor) {
      params.author = this.data.searchAuthor;
    }
    if (this.data.searchTitle) {
      params.title = this.data.searchTitle;
    }
    
    const result = await ShareService.getPoems(params);
    
    if (result.code === 0) {
      const { items, total, page, page_size } = result.data;
      this.setData({
        poems: items,
        total: total,
        hasMore: page * page_size < total
      });
    }
  } catch (error) {
    console.error('获取诗词列表失败:', error);
    wx.showToast({
      title: '加载失败',
      icon: 'error'
    });
  }
}

// 加载更多
async loadMore() {
  if (!this.data.hasMore) return;
  
  this.setData({
    currentPage: this.data.currentPage + 1
  });
  
  await this.loadPoems();
}
```

### 5.4 分享服务封装

**`apis/services/share.ts`**

```typescript
export class ShareService {
  // 记录分享关系
  static async recordShare(params: {
    sharer_user_id: string;
    share_type: string;
  }) {
    return await request.post('/api/share/record', params);
  }
  
  // 激活分享关系
  static async activateShare(params: {
    device_id?: string;
  }) {
    return await request.post('/api/share/activate', params);
  }
  
  // 获取我的邀请记录
  static async getMyInvites() {
    return await request.get('/api/share/my-invites');
  }
  
  // 获取我的邀请人
  static async getMyInviters() {
    return await request.get('/api/share/my-inviters');
  }
  
  // 获取解锁进度
  static async getUnlockProgress() {
    return await request.get('/api/share/unlock-progress');
  }
  
  // 生成分享码
  static async generateShareCode(params: {
    share_type: string;
    page: string;
    scene: string;
  }) {
    return await request.post('/api/share/generate-code', params);
  }
  
  // 获取诗词列表（分页）
  static async getPoems(params?: {
    author?: string;
    title?: string;
    sort_by?: string;
    order?: 'asc' | 'desc';
    page?: number;
    page_size?: number;
  }) {
    return await request.get('/api/share/poems', { params });
  }
}
```

## 六、邀请关系示例

### 6.1 数据示例

假设有以下分享关系：

| share_record_id | sharer_user_id | invitee_user_id | status    | activated_at | reward_unlocked_count |
|----------------|----------------|-----------------|-----------|--------------|----------------------|
| 1              | user_A         | user_B          | activated | 2024-01-15   | 10                   |
| 2              | user_A         | user_D          | pending   | NULL         | 0                    |
| 3              | user_C         | user_B          | activated | 2024-01-16   | 10                   |

### 6.2 查询结果示例

**用户A的邀请记录（`GET /api/share/my-invites`）：**
- 用户B：已激活，奖励 +10首
- 用户D：未激活

**用户B的邀请人（`GET /api/share/my-inviters`）：**
- 用户A：已激活
- 用户C：已激活

## 七、注意事项

1. **防重复激活**：同一个分享关系只能激活一次
2. **防自己邀请自己**：`sharer_user_id` 不能等于 `invitee_user_id`
3. **激活条件**：必须完成设备绑定才能激活
4. **解锁进度**：按增量记录，展示时按顺序从1开始编号
5. **奖励配置**：解锁奖励数量使用代码常量（默认10首），如需调整修改代码即可

## 八、后续扩展

1. **分享奖励阶梯**：不同数量的激活可获得不同奖励
2. **分享排行榜**：展示分享达人榜单
3. **分享有效期**：设置分享关系的有效期（如30天未激活则过期）
4. **多级分享**：支持二级、三级分享关系
5. **分享素材优化**：根据用户画像生成个性化分享海报
