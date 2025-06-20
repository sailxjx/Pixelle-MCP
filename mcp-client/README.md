# MCP Client

基于 Chainlit 构建的 MCP 客户端，提供友好的 Web 界面与各种 MCP 服务进行交互。

## 🚀 快速启动

```bash
# 安装依赖
uv sync

# 启动服务
./start.sh
```

访问: http://localhost:9003

## 📋 功能特性

- 🌐 Web 界面聊天交互
- 🔌 MCP 协议支持
- 📎 文件上传处理
- 🎨 多种 AIGC 工具集成
- ⚙️ 灵活的配置管理

## 🔧 配置说明

主要配置通过环境变量控制，可创建 `.env` 文件：

```env
CHAINLIT_CHAT_LLM=gpt-4  # 聊天模型
# 其他配置...
```

## 🛠️ 开发

```bash
# 开发模式启动
chainlit run main.py --port 9003 --host 0.0.0.0 -w
```

## 📁 项目结构

- `main.py` - 主入口文件
- `mcp_tool_handler.py` - MCP 工具处理器
- `starters.py` - 启动器配置
- `upload_util.py` - 文件上传工具
- `public/` - 静态资源
