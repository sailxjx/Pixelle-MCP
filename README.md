# 🎨 Pixelle MCP

> ✨ 基于 MCP 协议的 AIGC 方案，0代码将 ComfyUI 工作流转化为 Agent 工具，让 LLM 与 ComfyUI 强强联合。

<效果演示 | 待补充>

## 📁 项目结构

- **mcp-client**: 🌐 MCP 客户端，基于 Chainlit 构建的 Web 界面
- **mcp-server**: 🗄️ MCP 服务端，提供各种 AIGC 工具和服务

## 🚀 功能特性

- [x] 🔄 支持TISV（Text、Image、Sound/Speech、Video）全模态的互转和生成
- [x] 🧩 底层基于[ComfyUI](https://github.com/comfyanonymous/ComfyUI)实现，继承ComfyUI的开放生态下的所有能力
- [x] 🔧 制定并实现了 Workflow 即 MCP Tool 的方案，0代码开发，即可动态添加新的 MCP Tool
- [x] 🔌 server端基于[MCP](https://modelcontextprotocol.io/introduction)协议提供功能支持，支持任意mcp client集成（包含但不限于Cursor、Claude Desktop等）
- [x] 💻 client端基于[Chaintlit](https://github.com/Chainlit/chainlit)框架开发，继承了Chainlit的UI交互控件，支持集成更多的MCP Server



## 🏃‍♂️ 快速开始

### 📥 1. 克隆源码 & 更改配置

#### 📦 1.1 克隆源码

```shell
git clone https://github.com/AIDC-AI/Pixelle-MCP.git
cd Pixelle-MCP
```

#### 🗄️ 1.2 更改服务端配置

```shell
cd mcp-server
cp .env.example .env
# 按需更改.env的配置
```

#### 🌐 1.3 更改客户端配置

```shell
cd mcp-client
cp .env.example .env
# 按需更改.env的配置
```

### 🔧 2. 添加MCP Tool（可选）

这一步是可选的，只会决定你Agent的能力，不影响正常对话，如果你暂时不需要，可以先跳过。

`mcp-server/workflows`中是我们默认提供的一套目前比较热门的工作流，运行如下命令可以将其拷贝到你的mcp-server中，服务启动时会自动将其转化为MCP Tool，供大模型调用。

**注：这里强烈建议在拷贝之前，先将工作流拖进你的ComfyUI画布试运行，以确保后续调用过程中能够顺利执行。**

```shell
cp -r mcp-server/workflows mcp-server/data/custom_workflows
```

### 🚀 3. 启动服务

#### 🐳 3.1 Docker方式启动（推荐）

```shell
docker compose --profile all up -d
```

运行完成之后，对应这几个服务都会开启：

- **客户端**: 🌐 http://localhost:9003 (Chainlit Web UI)
- **服务端**: 🗄️ http://localhost:9002/sse (MCP Server)
- **MinIO**: 📦 http://localhost:9001 (对象存储管理界面)

#### 🛠️ 3.2 源码方式启动

a. 📦 自行运行 [minio](https://github.com/minio/minio) 服务，并更改`mcp-client/.env`和`mcp-server/.env`中对应的Minio配置

b. 🐍 安装 [uv](https://github.com/astral-sh/uv) 环境

c. 🗄️ 启动服务端

```shell
# 进入目录
cd mcp-server
# 安装依赖 (仅首次或更新时需要)
uv sync
# 启动服务
uv run main.py
```

d. 🌐 启动客户端

```shell
# 进入目录
cd mcp-client
# 安装依赖 (仅首次或更新时需要)
uv sync
# 启动服务
uv run main.py
```



## 🛠️ 添加自己的MCP Tool

⚡ 一个工作流即为提个MCP Tool

### 🎯 1. 添加最简单的MCP Tool

* 📝 在ComfyUI中搭建一个实现图片高斯模糊的工作流（[点击获取](docs/i_blur_ui.json)），然后将 `LoadImage `节点的 title 改为 `$image.image!`，如下图
![](docs/easy-workflow.png)

* 📤 然后将其导出为api格式文件，并重命名为 `i_blur.json`，你可以自己导出，也可以直接使用我们为你导出好的（[点击获取](docs/i_blur.json)）

* 📋 复制导出的API格式工作流文件（注：务必是API格式的），在web页面输入，并LLM添加这个Tool

  ![](docs/ready_to_send.png)

* ✨ 消息发送后，LLM会让将这个工作流自动转化为一个MCP Tool

  ![](docs/added_mcp.png)

* 🎨 此时，刷新页面，再发送任意图片，即可实现基于LLM进行的高斯模糊处理

  ![](docs/use_mcp_tool.png)

### 🔌 2. 添加复杂的MCP Tool

📊 添加MCP Tool的步骤和前面一样，唯一不一样的就是工作流部分（点击下载工作流：[UI格式](docs/t2i_by_flux_turbo_ui.json) 和 [API格式](docs/t2i_by_flux_turbo.json)）

![](docs/t2i_by_flux_turbo.png)


## 🔧 更多自定义配置

<待补充>



## 🙏 致谢

❤️ 衷心感谢以下所有组织、项目和团队，为本项目的发展和落地提供了支持。

* 🧩 [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
* 💬 [Chainlit](https://github.com/Chainlit/chainlit)
* 🗄️ [Minio](https://github.com/minio/minio)
* 🔌 [MCP](https://modelcontextprotocol.io/introduction)
* 🎬 [WanVideo](https://github.com/Wan-Video/Wan2.1)
* ⚡ [Flux](https://github.com/black-forest-labs/flux)



## 🤝 如何参与共建

我们欢迎所有形式的贡献！无论您是开发者、设计师还是用户，都可以通过以下方式参与项目建设：

### 🐛 报告问题
* 📋 在 [Issues](https://github.com/AIDC-AI/Pixelle-MCP/issues) 页面提交 Bug 报告
* 🔍 提交前请先搜索是否已有相似问题
* 📝 请详细描述问题的复现步骤和环境信息

### 💡 功能建议
* 🚀 在 [Issues](https://github.com/AIDC-AI/Pixelle-MCP/issues) 中提交功能请求
* 💭 描述您希望添加的功能及其使用场景
* 🎯 解释该功能如何改善用户体验

### 🔧 代码贡献

#### 📋 贡献流程
1. 🍴 Fork 本仓库到您的 GitHub 账户
2. 🌿 创建功能分支：`git checkout -b feature/your-feature-name`
3. 💻 进行开发并添加相应的测试
4. 📝 提交更改：`git commit -m "feat: add your feature"`
5. 📤 推送到您的仓库：`git push origin feature/your-feature-name`
6. 🔄 创建 Pull Request 到主仓库

#### 🎨 代码规范
* 🐍 Python 代码遵循 [PEP 8](https://pep8.org/) 规范
* 📖 为新功能添加适当的文档和注释

### 🧩 贡献工作流
* 📦 分享您的 ComfyUI 工作流到社区
* 🛠️ 提交经过测试的工作流文件
* 📚 为工作流添加使用说明和示例

### 💬 社区交流
* 🎯 参与 [Discussions](https://github.com/AIDC-AI/Pixelle-MCP/discussions) 讨论
* 💡 分享使用经验和最佳实践
* 🤝 帮助其他用户解决问题

### 📋 开发环境
参考 [快速开始](#-快速开始) 部分搭建开发环境，推荐使用源码方式启动进行开发调试。

感谢您对 Pixelle MCP 项目的关注和支持！🙏

