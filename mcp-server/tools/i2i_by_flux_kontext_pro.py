import random
from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow
from utils.image_util import detect_image_aspect_ratio

@mcp_tool
async def i2i_by_flux_kontext_pro(
    image: str = Field(description="The image to generate the image, must be a url"),
    prompt: str = Field(description="The prompt to generate the image, must be english"),
):
    """
    Edit existing images using text instructions with FLUX Kontext Pro model.
    If user gives multiple images, you need call image_merge tool to merge them into one image first, then use this tool to edit the merged image.
    
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
    result = await execute_workflow(__file__, {
        "image": image,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "seed": seed,
    })
    return result.to_llm_result() 