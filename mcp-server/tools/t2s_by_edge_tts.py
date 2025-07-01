from typing import Optional
from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
async def t2s_by_edge_tts(
    text: str = Field(description="The text to generate the audio"),
    voice: Optional[str] = Field("zh-CN-YunxiNeural", description="The voice of the audio, must be one of the following: 'zh-CN-YunxiNeural'、'zh-CN-YunjianNeural'"),
):
    """
    [ALTERNATIVE CHOICE] Convert text to speech using Edge TTS.
    
    Examples:
    - "你好，我是小明，很高兴认识你"
    """
    result = await execute_workflow(__file__, {
        "text": text,
        "voice": voice,
    })
    return result.to_llm_result() 