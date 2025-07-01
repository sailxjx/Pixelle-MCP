from typing import Optional, Literal
from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
async def i2v_by_kling_start_frame(
    image: str = Field(description="The image to generate the image, must be a url"),
    prompt: str = Field(description="The prompt to generate the image, support Chinese and English"),
    model_name: Optional[Literal["kling-v1", "kling-v1-5", "kling-v1-6", "kling-v2-master"]] = Field("kling-v1-6", description="The model name, must be one of the following: 'kling-v1', 'kling-v1-5', 'kling-v1-6', 'kling-v2-master'"),
    mode: Optional[Literal["std", "pro"]] = Field("std", description="The mode of the video, must be one of the following: 'std', 'pro'"),
):
    """
    [ALTERNATIVE CHOICE] Generate video from image using Kling Start Frame model.
    
    ** ONLY USE THIS MODEL WHEN USER SPECIFICALLY REQUESTS KLING **
    The default and preferred model for i2v is WAN2.1 FusionX.
    
    This tool creates a video from a single image based on your text prompt.
    The video will be generated with a smooth transition and a natural flow.
    
    提示词技巧：详细描述动作、表情、镜头运动和环境变化
    
    示例：
    - "让图片中的人物缓缓转头微笑，头发随风飘动"
    - "猫咪慢慢眨眼，尾巴轻轻摆动，阳光洒在毛发上"
    - "镜头从远景拉近到特写，人物深呼吸后微笑挥手"
    - "Camera slowly zooms in while the person smiles and waves"
    - "Wind gently blows through hair as the character looks into distance"
    """
    result = await execute_workflow(__file__, {
        "image": image,
        "prompt": prompt,
        "model_name": model_name,
        "mode": mode,
    })
    return result.to_llm_result() 