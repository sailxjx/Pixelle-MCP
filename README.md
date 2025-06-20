# Pixel MCP

这是一个基于 MCP (Model Context Protocol) 的 AIGC 工具集合项目，采用 monorepo 架构管理。

## 🏗️ 项目结构

- **mcp-client/**: MCP 客户端，基于 Chainlit 构建的 Web 界面
- **mcp-server/**: MCP 服务端，提供各种 AIGC 工具和服务

## 🚀 部署方式

本项目支持本地和 Docker 两种部署方式：

### 本地部署

#### 1. 纯客户端部署
仅部署 Web 界面，连接外部 MCP 服务
```bash
cd mcp-client
./start.sh
```

#### 2. 纯服务端部署
仅部署 MCP 服务，供其他客户端连接
```bash
cd mcp-server
./start.sh
```

#### 3. 完整部署 (client + server)
同时部署客户端和服务端，完整的本地环境
```bash
# 先启动服务端
cd mcp-server && ./start.sh

# 再启动客户端
cd ../mcp-client && ./start.sh
```

### Docker 部署

#### 1. 纯客户端 Docker 部署
```bash
cd mcp-client
docker-compose up -d
```

#### 2. 纯服务端 Docker 部署
```bash
cd mcp-server
docker-compose up -d
```

#### 3. 完整 Docker 部署 (client + server)

方式一：分别启动
```bash
# 先启动服务端
cd mcp-server && docker-compose up -d

# 再启动客户端
cd ../mcp-client && docker-compose up -d
```

方式二：一键启动（推荐）
```bash
# 使用完整配置文件一键启动所有服务
docker-compose -f docker-compose.full.yml up -d
```

## 📋 服务信息

- **客户端**: http://localhost:9003 (Chainlit Web UI)
- **服务端**: http://localhost:9002 (MCP Server)
- **MinIO**: http://localhost:9001 (对象存储管理界面)

## 🛠️ 开发环境

- Python 3.11+
- UV 包管理器
- Docker & Docker Compose (服务端)

## 📁 详细说明

每个子项目都有独立的 README 和配置：
- [mcp-client/README.md](mcp-client/README.md) - 客户端详细说明
- [mcp-server/README.md](mcp-server/README.md) - 服务端详细说明
