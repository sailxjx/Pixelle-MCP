# MCP Server

基于 MCP 协议的 AIGC 工具服务端，提供图像生成、语音合成、图像处理等多种 AI 能力。

## 🚀 快速启动

### Docker 部署 (推荐)

```bash
# 启动服务
./start.sh
```

### 本地开发

```bash
# 安装依赖
uv sync

# 启动服务
python main.py
```

访问:
- MCP 服务: http://localhost:9002
- MinIO 管理: http://localhost:9001

## 🛠️ 服务组件

- **MCP Server**: 核心服务，端口 9002
- **MinIO**: 对象存储服务，端口 9000/9001
- **自动初始化**: 创建存储桶和权限配置

## 📋 工具功能

- 🎨 **图像生成**: 文本转图像、图像编辑
- 🔊 **语音合成**: Edge TTS 中文语音
- 🖼️ **图像处理**: 裁剪、上传、格式转换
- 📹 **视频生成**: 图像转视频
- ☁️ **云存储**: MinIO 对象存储

## 🔧 环境配置

创建 `.env` 文件配置服务：

```env
# MinIO 配置
MINIO_USERNAME=admin
MINIO_PASSWORD=password123
MINIO_BUCKET=aigc-bucket

# MCP 服务配置
MCP_HOST=0.0.0.0
MCP_PORT=9002
```

## 📁 项目结构

- `main.py` - 服务入口
- `tools/` - MCP 工具实现
- `utils/` - 工具函数
- `resources/` - 资源文件
- `docker-compose.yml` - Docker 配置
