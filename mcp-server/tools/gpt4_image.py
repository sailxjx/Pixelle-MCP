from pydantic import Field
from typing import List, Union
from core import mcp_tool
from utils.gpt4_image_util import gpt_image_edit_by_curl
from utils.upload_util import upload


# @mcp_tool
async def generate_image_by_gpt4(
    image_urls: str = Field(description="The URLs of the origin images, split by line break if there are multiple images"),
    prompt: str = Field(description="The prompt to generate the image"),
):
    """Edit image by GPT-4"""
    image_url_list = image_urls.split('\n')
    result = await gpt_image_edit_by_curl(prompt, image_urls=image_url_list)
    if not result.success:
        return {
            "success": False,
            "msg": result.msg
        }
    
    url = upload(result.output_path)
    return {
        "success": True,
        "output_url": url
    }