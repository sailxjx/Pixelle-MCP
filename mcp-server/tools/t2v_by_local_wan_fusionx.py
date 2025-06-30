from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
def t2v_by_local_wan_fusionx(
    prompt: str = Field(description="The prompt to generate the video, must be english"),
    width: int = Field(512, description="The width of the video"),
    height: int = Field(288, description="The height of the video"),
):
    """
    Generate high-quality videos from text prompts using local WAN2.1 FusionX model.

    Creates completely new videos with exceptional detail, style diversity, and prompt adherence.
    The model excels at photorealistic scenes, artistic styles, and complex compositions.

    About parameters:
    - default video size: 512x288 (recommended), use 1024x576 only when user explicitly requests high quality.

    Prompt writing tips for best results:
    1. Length and Detail: Keep prompts around 80–100 words long, offering rich descriptions to support layered and vivid video output.
    2. Camera Movement: Clearly describe how the camera moves, such as tracking shots, pan left/right, dolly in/out, or tilt up/down. Avoid fast movements like whip pans or crash zooms, which Wan 2.1 struggles to render properly.
    3. Lighting and Shadows: Define lighting styles and sources—use terms like soft light, hard light, backlight, and volumetric lighting to shape the scene's atmosphere and depth.
    4. Atmosphere and Mood: Each prompt should convey a clear emotional tone such as somber, mysterious, dreamlike, or euphoric, enhancing the storytelling power of the visuals.
    5. Composition and Perspective: Use cinematic framing techniques like close-ups, wide shots, low angles, or high angles to emphasize focus and perspective in the scene.
    6. Visual Style: Incorporate stylistic cues such as cinematic, vintage film look, shallow depth of field, or motion blur to give the video a unique, cohesive aesthetic.
    7. Time and Environmental Context: Include relevant context such as time of day (e.g., dawn, dusk), weather conditions (e.g., rain, fog), and setting (e.g., forest, city, coast) to enhance realism and immersion.
    """
    result = execute_workflow("t2v_by_wan_fusionx.json", {
        "prompt": prompt,
        "width": width,
        "height": height,
    })
    return result.to_llm_result() 