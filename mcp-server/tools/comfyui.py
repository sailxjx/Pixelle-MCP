import random
from typing import Literal, Optional
from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow
from utils.image_util import detect_image_aspect_ratio

@mcp_tool
def t2i_by_local_flux(
    prompt: str = Field(description="The prompt to generate the image, must be english"),
    width: int = Field(512, description="The width of the image"),
    height: int = Field(512, description="The height of the image"),
):
    """
    Generate high-quality images from text prompts using local FLUX 1.1 model.
    
    Creates completely new images with exceptional detail, style diversity, and prompt adherence.
    The model excels at photorealistic scenes, artistic styles, and complex compositions.
    
    Prompt writing tips for best results:
    - Be detailed and specific: include colors, mood, lighting, and composition
    - Use natural language and full sentences rather than keywords
    - For photos: mention camera type, settings (e.g., "shot on DSLR, f/2.8, golden hour")
    - For portraits: describe features, expressions, clothing, and background
    - For scenes: specify foreground, middle ground, and background elements
    
    Excellent prompt examples:
    - "birthday, girl selfie with bright smile and colorful balloons"
    - "Close-up portrait of a child with bright vivid emotions, sparkling eyes full of joy, sunlight dancing on rosy cheeks"
    - "Serene lake reflecting dense forest during golden hour, shot on DSLR with wide-angle lens, f/8, perfect symmetry"
    - "Vintage travel poster for Paris, Eiffel Tower silhouette in warm sunset colors, 'PARIS' in golden Art Deco font"
    - "Ethereal dragon with neon lightning crystal on head, glowing blue eyes, majestic wings spread wide"
    """
    seed = random.randint(0, 1000000)
    result = execute_workflow("flux_turbo.json", {
        "prompt": prompt,
        "width": width,
        "height": height,
        "seed": seed,
    })
    return result.to_llm_result()

@mcp_tool
def i2i_by_flux_kontext_pro(
    image: str = Field(description="The image to generate the image, must be a url"),
    prompt: str = Field(description="The prompt to generate the image, must be english"),
):
    """
    Edit existing images using text instructions with FLUX Kontext Pro model.
    
    Modifies existing images based on your text instructions. You can change objects, 
    remove elements, alter text, modify colors, and more.
    
    Example instructions based on official FLUX playground:
    - "remove the people from the background"
    - "change the drink to a virgin colada"
    - "the frog is now a panda and replace 'ULTRA' by 'KONTEXT'"
    - "camera is closer to the cat who's now looking at the camera"
    - "she's now holding an orange umbrella and smiling"
    - "replace 'joy' by 'BFL'"
    - "give the ball stick man cartoon arms and legs and a simplistic face"
    - "Style the lizard as woven out of string or yarn — crafty, textile feel"
    """
    # 自动检测图片的宽高比
    aspect_ratio = detect_image_aspect_ratio(image)
    
    seed = random.randint(0, 1000000)
    result = execute_workflow("flux_kontext_pro.json", {
        "image": image,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "seed": seed,
    })
    return result.to_llm_result()

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

@mcp_tool
def i2v_by_kling_start_frame(
    image: str = Field(description="The image to generate the image, must be a url"),
    prompt: str = Field(description="The prompt to generate the image, support Chinese and English"),
    model_name: Optional[Literal["kling-v1", "kling-v1-5", "kling-v1-6", "kling-v2-master"]] = Field("kling-v1-6", description="The model name, must be one of the following: 'kling-v1', 'kling-v1-5', 'kling-v1-6', 'kling-v2-master'"),
    mode: Optional[Literal["std", "pro"]] = Field("std", description="The mode of the video, must be one of the following: 'std', 'pro'"),
):
    """
    Generate video from image using Kling Start Frame model.
    
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
    result = execute_workflow("i2v_kling_start_frame.json", {
        "image": image,
        "prompt": prompt,
        "model_name": model_name,
        "mode": mode,
    })
    return result.to_llm_result()

# @mcp_tool
def t2s_by_edge_tts(
    text: str = Field(description="The text to generate the audio"),
    voice: Optional[str] = Field("zh-CN-YunxiNeural", description="The voice of the audio, must be one of the following: 'zh-CN-YunxiNeural'、'zh-CN-YunjianNeural'"),
):
    """
    Convert text to speech using Edge TTS.
    
    Examples:
    - "你好，我是小明，很高兴认识你"
    """
    result = execute_workflow("t2s_edge_tts.json", {
        "text": text,
        "voice": voice,
    })
    return result.to_llm_result()
