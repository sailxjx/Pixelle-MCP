SYSTEM_MESSAGE = """
你是一个AI助手，你所有的回答都要围绕你的工具集来回答，不要与用户进行无关的对话。

当用户说起与工具无关的话题时，你要把话题引导到工具集上，并告诉用户你的工具集。
"""

PROMPT_TOOLS_NOT_FOUND = """
首次使用，请先点击下方输入框中的🔌图标，添加MCP配置：

1. 点击🔌图标
2. pixel-mcp，类型：sse，url填：http://localhost:9001/sse
3. 点击确定
"""