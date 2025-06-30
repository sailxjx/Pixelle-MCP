from pydantic import Field
from core import mcp_tool
from utils.comfyui_util import execute_workflow

@mcp_tool
def i2t_by_local_florence(
    image: str = Field(description="The image to generate the text, must be a url"),
):
    """
    Generate high-quality text descriptions from images using local Florence model.
    
    Main use cases:
    1. **Reverse image prompt generation**:
       - When users upload an image and want to get prompts for AI art generation
       - Analyzes visual elements, style, composition, etc. to generate prompts for Stable Diffusion, DALL-E, and other models
       - In this case, return the tool's raw output directly to users without any modification or summary
       - Users can directly use these prompts for image generation
    2. **Image content understanding**:
       - When users ask about specific content, objects, scenes, people, etc. in the image
       - Need to understand the semantic content of the image and answer users' specific questions
       - In this case, combine tool output with conversation context to give users contextually appropriate natural responses
       - Don't return raw output directly, but provide targeted replies based on understanding results
    """
    result = execute_workflow("i2t_by_local_florence.json", {
        "image": image,
    })
    return result.to_llm_result() 