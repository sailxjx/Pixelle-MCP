# Pixel MCP

这是一个基于 MCP (Model Context Protocol) 的 AIGC 工具集合项目，采用 monorepo 架构管理。

## 🏗️ 项目结构

- **mcp-client/**: MCP 客户端，基于 Chainlit 构建的 Web 界面
- **mcp-server/**: MCP 服务端，提供各种 AIGC 工具和服务

## 🚀 快速启动

### 一键部署（推荐）

```bash
# 部署所有服务
./redeploy.sh

# 仅重启服务端
./redeploy.sh server

# 仅重启客户端
./redeploy.sh client

# 强制重新构建
./redeploy.sh -f

# 查看帮助
./redeploy.sh -h
```

### 手动部署

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 停止所有服务
docker-compose down

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 📋 服务信息

部署完成后，可以通过以下地址访问：

- **客户端**: http://localhost:9003 (Chainlit Web UI)
- **服务端**: http://localhost:9002 (MCP Server)
- **MinIO**: http://localhost:9001 (对象存储管理界面)

## 🛠️ 环境配置

### 服务端配置

创建 `mcp-server/.env` 文件：

```env
# MinIO 配置
MINIO_USERNAME=admin
MINIO_PASSWORD=password123
MINIO_BUCKET=aigc-bucket

# MCP 服务配置
MCP_HOST=0.0.0.0
MCP_PORT=9002

# 外部服务（可选）
COMFYUI_BASE_URL=http://your-comfyui-server
COMFYUI_API_KEY=your-api-key
```

### 客户端配置

创建 `mcp-client/.env` 文件：

```env
# Chainlit 配置
CHAINLIT_CHAT_LLM=gpt-4
CHAINLIT_HOST=0.0.0.0
CHAINLIT_PORT=9003
```

## 🔧 开发环境

- Python 3.11+
- UV 包管理器
- Docker & Docker Compose

## 📁 详细说明

每个子项目都有独立的 README 和配置：
- [mcp-client/README.md](mcp-client/README.md) - 客户端详细说明
- [mcp-server/README.md](mcp-server/README.md) - 服务端详细说明

## 🎯 功能特性

### MCP 客户端
- 🌐 Web 界面聊天交互
- 🔌 MCP 协议支持
- 📎 文件上传处理
- 🎨 多种 AIGC 工具集成

### MCP 服务端
- 🎨 **图像生成**: 文本转图像、图像编辑
- 🔊 **语音合成**: Edge TTS 中文语音
- 🖼️ **图像处理**: 裁剪、上传、格式转换
- 📹 **视频生成**: 图像转视频
- ☁️ **云存储**: MinIO 对象存储

## 🚀 快速体验

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd pixel-mcp
   ```

2. **配置环境**
   ```bash
   # 复制环境变量模板（如果需要）
   cp mcp-server/.env.example mcp-server/.env
   cp mcp-client/.env.example mcp-client/.env
   ```

3. **一键启动**
   ```bash
   ./redeploy.sh
   ```

4. **访问服务**
   - 打开浏览器访问: http://localhost:9003
   - 开始使用 AIGC 工具！
