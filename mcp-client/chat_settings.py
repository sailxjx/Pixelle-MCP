from core import logger
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider, TextInput


async def setup_chat_settings():
    # 文档：https://docs.chainlit.io/api-reference/chat-settings#usage
    settings = await cl.ChatSettings(
        [
            # TextInput(
            #     id="comfyui_base_url",
            #     label="ComfyUI服务地址",
            #     initial="http://localhost:8188",
            #     placeholder="请输入ComfyUI的服务地址，如：http://localhost:8188",
            # ),
        ]
    ).send()
    logger.info(f"chat settings: {settings}")


async def setup_settings_update(settings):
    logger.info(f"on_settings_update: {settings}")