from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
async def s2t_by_local_whisper(
    audio: str = Field(description="The audio to generate the text, must be a url"),
):
    """
    Recognize speech from audio using local Whisper model.
    """
    result = await execute_workflow(__file__, {
        "audio": audio,
    })
    return result.to_llm_result() 