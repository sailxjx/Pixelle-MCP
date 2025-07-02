from typing import Literal
from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
async def v2s_by_extract(
    video: str = Field(description="The video to extract the audio, must be a url"),
):
    """
    Extract audio from video.
    """
    
    result = await execute_workflow(__file__, {
        "video": video,
    })
    return result.to_llm_result() 