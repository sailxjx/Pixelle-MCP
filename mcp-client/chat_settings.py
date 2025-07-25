# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import re
from core import logger
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider, TextInput, Tags
from prompt import DEFAULT_SYSTEM_PROMPT


async def setup_chat_settings():
    # 文档：https://docs.chainlit.io/api-reference/chat-settings#usage
    
    settings = await cl.ChatSettings(
        [
            TextInput(
                id="system_prompt",
                label="系统提示词",
                initial=DEFAULT_SYSTEM_PROMPT,
                multiline=True,
                placeholder="请输入系统提示词，用于指导AI助手的行为和回复方式。",
            ),
            # Tags(
            #     id="OpenAI_Models",
            #     label="OpenAI - Models",
            #     initial=["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4.1-2025-04-14-GlobalStandard"],
            #     values=["gpt-4.1-2025-04-14-GlobalStandard"],
            # ),
            # TextInput(
            #     id="comfyui_base_url",
            #     label="ComfyUI服务地址",
            #     initial="http://localhost:8188",
            #     placeholder="请输入ComfyUI的服务地址，如：http://localhost:8188",
            # ),
            # Select(
            #     id="Default_OpenAI_Model",
            #     label="Default OpenAI Model",
            #     values=openai_models,
            #     initial_index=0,
            # ),
            # Switch(id="Streaming", label="OpenAI - Stream Tokens", initial=True),
            # Slider(
            #     id="Temperature",
            #     label="OpenAI - Temperature",
            #     initial=1,
            #     min=0,
            #     max=2,
            #     step=0.1,
            # ),
            # Slider(
            #     id="SAI_Steps",
            #     label="Stability AI - Steps",
            #     initial=30,
            #     min=10,
            #     max=150,
            #     step=1,
            #     description="Amount of inference steps performed on image generation.",
            # ),
            # Slider(
            #     id="SAI_Cfg_Scale",
            #     label="Stability AI - Cfg_Scale",
            #     initial=7,
            #     min=1,
            #     max=35,
            #     step=0.1,
            #     description="Influences how strongly your generation is guided to match your prompt.",
            # ),
            # Slider(
            #     id="SAI_Width",
            #     label="Stability AI - Image Width",
            #     initial=512,
            #     min=256,
            #     max=2048,
            #     step=64,
            #     tooltip="Measured in pixels",
            # ),
            # Slider(
            #     id="SAI_Height",
            #     label="Stability AI - Image Height",
            #     initial=512,
            #     min=256,
            #     max=2048,
            #     step=64,
            #     tooltip="Measured in pixels",
            # ),
        ]
    ).send()
    logger.debug(f"chat settings: {settings}")


async def setup_settings_update(settings):
    logger.debug(f"on_settings_update: {settings}")
    cl.user_session.set("settings", settings)
    
    await _update_system_prompt_if_need(settings)

    
async def _update_system_prompt_if_need(settings):
    cl_messages = cl.chat_context.get()
    if not cl_messages:
        return
    
    first_message = cl_messages[0]
    if first_message.type != "system_message":
        return
    
    first_message.content = settings.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
    await first_message.update()
    logger.info(f"update system prompt: {first_message.content}")

