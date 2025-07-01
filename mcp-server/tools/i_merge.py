from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
async def i_merge(
    first_image: str = Field(description="The first image to merge, must be a url"),
    second_image: str = Field(description="The second image to merge, must be a url"),
):
    """
    Merge two images into one along the horizontal axis.
    
    It is generally used when a user has input multiple pictures, but the parameter of the tool is only one picture.
    For example, a user wants to generate image by kontext pro with multi reference images, and so on.
    """
    result = await execute_workflow(__file__, {
        "first_image": first_image,
        "second_image": second_image,
    })
    return result.to_llm_result() 