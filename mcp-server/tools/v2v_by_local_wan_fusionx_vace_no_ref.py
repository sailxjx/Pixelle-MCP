from typing import Literal
from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
async def v2v_by_local_wan_fusionx_vace_no_ref(
    video: str = Field(description="The video to generate the video, must be a url"),
    prompt: str = Field(description="The prompt to generate the video, support Chinese and English"),
    quality: Literal["low", "high"] = Field("low", description="Video quality: 'low' for faster generation, 'high' for better quality"),
):
    """
    Useful for generating videos from video using WAN2.1 FusionX Vace model without image reference.

    Example:
    - "Replace subject with a cat"

    Prompt writing tips for best results:
    1. Length and Detail: Keep prompts around 80–100 words long, offering rich descriptions to support layered and vivid video output.
    2. Camera Movement: Clearly describe how the camera moves, such as tracking shots, pan left/right, dolly in/out, or tilt up/down. Avoid fast movements like whip pans or crash zooms.
    3. Lighting and Shadows: Define lighting styles and sources—use terms like soft light, hard light, backlight, and volumetric lighting to shape the scene's atmosphere and depth.
    4. Atmosphere and Mood: Each prompt should convey a clear emotional tone such as somber, mysterious, dreamlike, or euphoric.
    5. Composition and Perspective: Use cinematic framing techniques like close-ups, wide shots, low angles, or high angles to emphasize focus and perspective.
    6. Visual Style: Incorporate stylistic cues such as cinematic, vintage film look, shallow depth of field, or motion blur.
    7. Time and Environmental Context: Include relevant context such as time of day, weather conditions, and setting to enhance realism and immersion.
    
    Return:
    - Returns two videos: the generated video and a comparison video (original vs generated side-by-side)
    - By default, show users the generated video result
    - If users specifically request to see the comparison video or both videos, provide accordingly
    """
    if quality == "low":
        size = 512
    elif quality == "high":
        size = 768
    else:
        raise ValueError(f"Invalid quality: `{quality}`")
    
    result = await execute_workflow(__file__, {
        "video": video,
        "prompt": prompt,
        "size": size,
    })
    return result.to_llm_result() 