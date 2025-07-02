import random
from typing import Literal
from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
async def s_generate_audio_by_prompt(
    prompt: str = Field(description="The prompt to generate the audio, must be english, for example: 'heaven church electronic dance music'"),
    seconds: int = Field(10, description="The seconds of the audio, must be a number, for example: 10.0"),
):
    """
    Generate audio based on prompt using Stable Audio Open 1.0
    """
    result = await execute_workflow(__file__, {
        "prompt": prompt,
        "seconds": seconds,
    })
    return result.to_llm_result() 