import chainlit as cl
from mcp import ClientSession
from message_converter import messages_from_chaintlit_to_openai
import starters
import auth
import os

from core import logger
from prompt import PROMPT_TOOLS_NOT_FOUND, SYSTEM_MESSAGE
from tool_converter import tools_from_chaintlit_to_openai
from mcp_tool_handler import handle_mcp_connect, handle_mcp_disconnect
from chat_settings import setup_chat_settings, setup_settings_update
import mcp_tool_handler as tool_handler
from upload_util import upload

CHAINLIT_CHAT_LLM = os.getenv("CHAINLIT_CHAT_LLM")

@cl.on_chat_start
async def start():
    """初始化聊天会话"""
    await setup_chat_settings()
    
    sys_message = cl.Message(
        type="system_message",
        content=SYSTEM_MESSAGE
    )
    cl.chat_context.add(sys_message)
    
@cl.on_settings_update
async def on_settings_update(settings):
    await setup_settings_update(settings)

@cl.on_mcp_connect
async def on_mcp(connection, session: ClientSession):
    """处理 MCP 连接"""
    await handle_mcp_connect(connection, session, tools_from_chaintlit_to_openai)
    
    cl.user_session.set("mcp_session", session)
    
    # pixel-mcp单独适配
    if connection.name == "pixel-mcp":
        result_resource = await session.read_resource("usage://tools")
        usage_tools = result_resource.contents[0].text
        if usage_tools:
            cl_messages = cl.chat_context.get()
            if usage_tools not in cl_messages[0].content:
                cl_messages[0].content = f"{SYSTEM_MESSAGE}\n\n{usage_tools}"
                await cl_messages[0].update()


@cl.on_mcp_disconnect
async def on_mcp_disconnect(name: str, session: ClientSession):
    """MCP 连接断开时调用"""
    logger.info(f"MCP 连接已断开: {name}")
    await handle_mcp_disconnect(name)


@cl.on_message
async def on_message(message: cl.Message):
    """处理用户消息"""
    # 检查是否为starter消息，如果已处理则直接返回
    is_handled = await starters.hook_by_starters(message)
    if is_handled:
        return
    
    need_update = False
    for element in message.elements:
        is_media = isinstance(element, cl.Image) \
            or isinstance(element, cl.Audio) \
            or isinstance(element, cl.Video)
        if is_media and element.path and not element.url:
            element.size = "small"
            element.url = upload(element.path, filename=element.name)
            need_update = True
    if need_update:
        await message.update()
    
    tools = tool_handler.get_all_tools()
    if not tools:
        logger.info("首次使用，请先点击下方输入框中的🔌图标，添加MCP配置")
        await cl.Message(content=PROMPT_TOOLS_NOT_FOUND).send()
        return
    
    cl_messages = cl.chat_context.get()
    messages = messages_from_chaintlit_to_openai(cl_messages)
    
    # 使用工具处理器处理流式响应和工具调用
    await tool_handler.process_streaming_response(
        messages=messages,
        model=CHAINLIT_CHAT_LLM,
    )


if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)
