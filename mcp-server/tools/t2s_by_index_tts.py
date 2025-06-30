from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
def t2s_by_index_tts(
    text: str = Field(description="The text to generate the audio"),
    # voice: Optional[str] = Field("default", description="The voice of the audio"),
):
    """
    [DEFAULT CHOICE] Convert text to speech using Edge TTS.
    
    Examples:
    - "你好，我是小明，很高兴认识你"
    """
    result = execute_workflow("t2s_by_index_tts.json", {
        "text": text,
        # "voice": voice,
    })
    return result.to_llm_result() 