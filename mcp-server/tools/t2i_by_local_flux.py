import random
from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
async def t2i_by_local_flux(
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
    result = await execute_workflow(__file__, {
        "prompt": prompt,
        "width": width,
        "height": height,
        "seed": seed,
    })
    return result.to_llm_result() 