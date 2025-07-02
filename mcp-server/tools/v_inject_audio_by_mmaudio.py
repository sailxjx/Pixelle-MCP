from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
async def v_inject_audio_by_mmaudio(
    video: str = Field(description="The video to inject audio, must be a url"),
    prompt: str = Field("", description="The positive prompt to generate audio, must be english"),
    negative_prompt: str = Field("", description="The negative prompt to generate audio, must be english"),
):
    """
    Generate audio based on video using MMAudio, and inject audio into video.
    
    DO NOT use `prompt` and `negative_prompt` parameter, except for user's special request.
    """
    result = await execute_workflow(__file__, {
        "video": video,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
    })
    return result.to_llm_result() 