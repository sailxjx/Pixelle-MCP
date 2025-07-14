# Pixelle MCP

这是一个基于 MCP (Model Context Protocol) 的 AIGC 工具集合项目，采用 monorepo 架构管理。

## 🏗️ 项目结构

- **mcp-client/**: MCP 客户端，基于 Chainlit 构建的 Web 界面
- **mcp-server/**: MCP 服务端，提供各种 AIGC 工具和服务

## 🚀 快速启动

### 远程部署（推荐）

使用 `redeploy.sh` 脚本可以方便地部署到远程服务器：

```bash
# 部署所有服务到远程服务器
./redeploy.sh

# 仅重启远程服务端
./redeploy.sh server

# 仅重启远程客户端
./redeploy.sh client

# 强制重新构建远程服务
./redeploy.sh -f

# 查看帮助
./redeploy.sh -h

# 使用自定义服务器
REMOTE_HOST=192.168.1.100 REMOTE_USER=user ./redeploy.sh
```

**默认远程服务器配置**：
- 服务器地址: `30.150.44.149`
- 用户名: `sss`
- 项目目录: `/home/sss/puke/workspace/pixelle-mcp`

可以通过环境变量自定义：
```bash
export REMOTE_HOST=your-server-ip
export REMOTE_USER=your-username
export PROJECT_DIR=/path/to/your/project
./redeploy.sh
```

### 本地部署

如果需要在本地部署，可以直接使用 Docker Compose：

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 停止所有服务
docker-compose down

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启特定服务
docker-compose restart mcp-server
docker-compose restart mcp-client
```

## 📋 服务信息

部署完成后，可以通过以下地址访问：

**远程部署**：
- **客户端**: http://30.150.44.149:9003 (Chainlit Web UI)
- **服务端**: http://30.150.44.149:9002 (MCP Server)
- **MinIO**: http://30.150.44.149:9001 (对象存储管理界面)

**本地部署**：
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

### 远程部署体验

1. **配置SSH连接**
   ```bash
   # 确保可以SSH连接到服务器
   ssh-copy-id user@server-ip
   ```

2. **设置环境变量**（可选）
   ```bash
   export REMOTE_HOST=your-server-ip
   export REMOTE_USER=your-username
   export PROJECT_DIR=/path/to/project
   ```

3. **一键部署**
   ```bash
   ./redeploy.sh
   ```

4. **访问服务**
   - 打开浏览器访问: http://your-server-ip:9003
   - 开始使用 AIGC 工具！

### 本地部署体验

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd pixelle-mcp
   ```

2. **配置环境**
   ```bash
   # 复制环境变量模板（如果需要）
   cp mcp-server/.env.example mcp-server/.env
   cp mcp-client/.env.example mcp-client/.env
   ```

3. **启动服务**
   ```bash
   docker-compose up -d --build
   ```

4. **访问服务**
   - 打开浏览器访问: http://localhost:9003
   - 开始使用 AIGC 工具！
