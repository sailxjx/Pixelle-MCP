from pydantic import Field
from core import mcp_tool
import os

from utils.upload_util import upload

@mcp_tool
def upload_file(
    file_path_or_url: str = Field(description="The path or url of the file to upload"),
):
    """Upload file to MinIO"""
    try:
        url = upload(file_path_or_url)
        return {
            "success": True,
            "url": url
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }