# Pixelle MCP Base

基于 FastAPI 的基础服务，提供文件存储和共用服务能力。

## 🏗️ 架构设计

- **存储抽象层**: 支持多种存储后端（本地文件系统等）
- **文件服务**: 提供统一的文件上传、下载、管理API
- **配置管理**: 灵活的配置系统，支持环境变量

## 🚀 快速开始

### 配置文件

创建 `.env` 文件：

```bash
# 基础服务配置
APP_NAME=Pixelle MCP Base
APP_VERSION=0.1.0
HOST=0.0.0.0
PORT=9001
DEBUG=false

# 存储配置
# 支持的存储类型: local
STORAGE_TYPE=local

# 本地存储配置（当STORAGE_TYPE=local时使用）
LOCAL_STORAGE_PATH=data/files

# 文件配置
MAX_FILE_SIZE=104857600  # 100MB

# API配置
API_PREFIX=/api
CORS_ORIGINS=["*"]
```

### 启动方式

#### Docker 启动
```bash
docker build -t pixelle-mcp-base .
docker run -p 9001:9001 pixelle-mcp-base
```

#### 源码启动
```bash
uv sync
uv run main.py
```

## 📖 API 文档

启动服务后访问：
- API 文档: http://localhost:9001/docs
- 健康检查: http://localhost:9001/health

### 主要端点

- `POST /api/upload` - 上传文件
- `GET /api/files/{file_id}` - 获取文件
- `GET /api/files/{file_id}/info` - 获取文件信息
- `DELETE /api/files/{file_id}` - 删除文件

## 🔧 存储后端

### 本地存储 (local)
- 文件存储在 `data/files/` 目录
- 零外部依赖
- 适合开发和小规模部署



## 🏗️ 目录结构

```
mcp-base/
├── config/           # 配置管理
├── storage/          # 存储抽象层
├── services/         # 业务服务层
├── main.py          # FastAPI应用入口
├── Dockerfile       # Docker构建文件
└── pyproject.toml   # Python项目配置
``` 