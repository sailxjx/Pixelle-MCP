import random
from typing import Literal
from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
def i2i_by_gpt4(
    image: str = Field(description="The image to generate the image, must be a url"),
    prompt: str = Field(description="The prompt to generate the image, support all languages"),
    quality: Literal["low", "medium", "high"] = Field("medium", description="The quality of the image, must be one of the following: 'low', 'medium', 'high'"),
):
    """
    Transform and edit images using GPT-4o's multimodal image generation.
    
    Features enhanced photorealism, accurate text rendering, and contextual understanding.
    Supports multiple languages and conversation-like iterative refinement.
    
    Prompting tips:
    - Use natural, descriptive language
    - Specify colors, lighting, mood, and perspective
    - For text in images: mention font style and placement
    - Be clear about desired style and atmosphere
    
    Quality levels:
    - low: Fast, draft quality
    - medium: Balanced (recommended)  
    - high: Best detail, slower
    
    Examples:
    - "Make this photo look like a watercolor painting"
    - "Change the background to a sunset sky"
    - "Add text 'WELCOME' in elegant font at the top"
    - "Convert to black and white vintage style"
    - "把这张照片改成中国水墨画风格"
    - "在图片顶部添加'欢迎光临'四个大字，使用毛笔字体"
    - "将背景换成樱花飞舞的春日场景"
    """
    seed = random.randint(0, 1000000)
    result = execute_workflow("i2i_gpt4.json", {
        "image": image,
        "prompt": prompt,
        "seed": seed,
        "quality": quality,
    })
    return result.to_llm_result() 