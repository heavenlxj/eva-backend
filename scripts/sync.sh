#!/bin/bash

# rsync 同步脚本 - 将 eva-backend 目录同步到远程服务器
# 使用方法: ./scripts/sync.sh [--dry-run]

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
SOURCE_DIR="/Users/apple/WeChatProjects/eva-backend"
REMOTE_HOST="root@182.92.23.188"
REMOTE_PATH="/root/xjliu/eva-backend"

# 检查是否为 dry-run 模式
DRY_RUN=""
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN="--dry-run"
    echo -e "${YELLOW}⚠️  运行在 DRY-RUN 模式（不会实际同步文件）${NC}\n"
fi

# 检查源目录是否存在
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ 错误: 源目录不存在: $SOURCE_DIR${NC}"
    exit 1
fi

# 显示配置信息
echo -e "${GREEN}📦 开始同步文件...${NC}"
echo -e "源目录: ${YELLOW}$SOURCE_DIR${NC}"
echo -e "目标: ${YELLOW}$REMOTE_HOST:$REMOTE_PATH${NC}"
echo ""

# rsync 命令
# 排除的文件和目录:
# - .git: Git 版本控制目录
# - __pycache__: Python 缓存目录
# - *.pyc: Python 编译文件
# - .DS_Store: macOS 系统文件
# - *.swp: Vim 临时文件
# - *.log: 日志文件
# - .env*.local: 本地环境变量文件
# - .idea: IDE 配置目录
# - src/logs: 日志目录
# - node_modules: Node.js 依赖（如果有）
# - .venv, venv: Python 虚拟环境
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.DS_Store' \
    --exclude='*.swp' \
    --exclude='*.log' \
    --exclude='.env*.local' \
    --exclude='.idea' \
    --exclude='src/logs' \
    --exclude='node_modules' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='*.egg-info' \
    --exclude='.pytest_cache' \
    --exclude='.mypy_cache' \
    --exclude='.coverage' \
    --exclude='htmlcov' \
    $DRY_RUN \
    "$SOURCE_DIR/" \
    "$REMOTE_HOST:$REMOTE_PATH/"

# 检查 rsync 执行结果
if [ $? -eq 0 ]; then
    if [ -z "$DRY_RUN" ]; then
        echo -e "\n${GREEN}✅ 同步完成！${NC}"
    else
        echo -e "\n${YELLOW}ℹ️  DRY-RUN 完成（未实际同步）${NC}"
        echo -e "${YELLOW}   如需实际同步，请运行: ./scripts/sync.sh${NC}"
    fi
else
    echo -e "\n${RED}❌ 同步失败！请检查错误信息。${NC}"
    exit 1
fi

