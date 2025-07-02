from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

OPTIONAL_MODELS = [
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4.1",
    "gpt-4o",
    "o1",
    "o1-pro",
    "o3",
    "o4-mini",
]

@mcp_tool
async def i2t_by_gpt(
    image: str = Field(description="The image to analyze, must be a url"),
    prompt: str = Field("Describe the image detailedly", description="The prompt to analyze"),
    model: str = Field(OPTIONAL_MODELS[0], description="The model to use, must be one of the following: " + ", ".join(OPTIONAL_MODELS)),
):
    """
    Analyze image using OpenAI's GPT model.
    """
    result = await execute_workflow(__file__, {
        "image": image,
        "prompt": prompt,
        "model": model,
    })
    return result.to_llm_result() 