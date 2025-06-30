from typing import Literal
from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow
from utils.image_util import detect_image_aspect_ratio_enum

@mcp_tool
def i2v_by_local_wan_fusionx(
    image: str = Field(description="The image to generate the video, must be a url"),
    prompt: str = Field(description="The prompt to generate the video, support Chinese and English"),
    quality: Literal["low", "high"] = Field("low", description="Video quality: 'low' for faster generation, 'high' for better quality"),
):
    """
    [DEFAULT CHOICE] Generate high-quality videos from image using WAN2.1 FusionX model.
    
    ** THIS IS THE PREFERRED AND DEFAULT MODEL FOR IMAGE-TO-VIDEO GENERATION **
    Use this model UNLESS the user specifically requests Kling model.

    Creates videos from input images with exceptional detail, style diversity, and prompt adherence.
    The model excels at photorealistic scenes, artistic styles, and complex compositions.
    
    The video dimensions are automatically determined based on the input image's aspect ratio:
    - Low quality: 512px on the long side (recommended for faster generation)
    - High quality: 1024px on the long side (use only when explicitly requested)

    支持中英文提示词，中文示例：
    - "让图片中的人物缓缓转头微笑，阳光洒在脸上"
    - "镜头从远景拉近到特写，人物深呼吸后挥手"
    - "猫咪慢慢眨眼，尾巴轻轻摆动，背景有微风吹过"
    
    English examples:
    - "Camera slowly zooms in while the person smiles and waves"
    - "Wind gently blows through hair as the character looks into distance"
    - "Slow motion of water droplets falling with soft lighting"

    Prompt writing tips for best results:
    1. Length and Detail: Keep prompts around 80–100 words long, offering rich descriptions to support layered and vivid video output.
    2. Camera Movement: Clearly describe how the camera moves, such as tracking shots, pan left/right, dolly in/out, or tilt up/down. Avoid fast movements like whip pans or crash zooms.
    3. Lighting and Shadows: Define lighting styles and sources—use terms like soft light, hard light, backlight, and volumetric lighting to shape the scene's atmosphere and depth.
    4. Atmosphere and Mood: Each prompt should convey a clear emotional tone such as somber, mysterious, dreamlike, or euphoric.
    5. Composition and Perspective: Use cinematic framing techniques like close-ups, wide shots, low angles, or high angles to emphasize focus and perspective.
    6. Visual Style: Incorporate stylistic cues such as cinematic, vintage film look, shallow depth of field, or motion blur.
    7. Time and Environmental Context: Include relevant context such as time of day, weather conditions, and setting to enhance realism and immersion.
    """
    # 检测输入图片的宽高比
    aspect_ratio = detect_image_aspect_ratio_enum(image)
    # 根据宽高比和质量获取具体的宽高尺寸
    width, height = aspect_ratio.get_dimensions(quality)
    
    result = execute_workflow("i2v_by_wan_fusionx.json", {
        "image": image,
        "prompt": prompt,
        "width": width,
        "height": height,
    })
    return result.to_llm_result() 