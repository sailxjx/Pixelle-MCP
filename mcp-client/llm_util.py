from enum import Enum
import os
from typing import Union

from pydantic import BaseModel, Field
from core import logger

# 默认模型
CHAINLIT_CHAT_DEFAULT_MODEL = os.getenv("CHAINLIT_CHAT_DEFAULT_MODEL")
logger.info(f"Default chat model: {CHAINLIT_CHAT_DEFAULT_MODEL}")


# OpenAI配置
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAINLIT_CHAT_OPENAI_MODELS = os.getenv("CHAINLIT_CHAT_OPENAI_MODELS")

openai_models = [model.strip() for model in CHAINLIT_CHAT_OPENAI_MODELS.split(",") if model.strip()]
logger.info(f"OPENAI_BASE_URL: {OPENAI_BASE_URL}")
logger.info(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
logger.info(f"Found {len(openai_models)} OpenAI models: {openai_models}")


# Ollama配置
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODELS = os.getenv("OLLAMA_MODELS")
OLLAMA_API_KEY = "ollama"

ollama_models = [model.strip() for model in OLLAMA_MODELS.split(",") if model.strip()]
logger.info(f"OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")
logger.info(f"Found {len(ollama_models)} Ollama models: {ollama_models}")


# 检查是否配置了模型
if not openai_models and not ollama_models:
    raise ValueError("No models found, please set CHAINLIT_CHAT_OPENAI_MODELS or OLLAMA_MODELS in .env")
if openai_models and not OPENAI_API_KEY:
    raise ValueError("No OpenAI API key found, please set OPENAI_API_KEY in .env")
if ollama_models and not OLLAMA_BASE_URL:
    raise ValueError("No Ollama base URL found, please set OLLAMA_BASE_URL in .env")


class ModelType(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    
class ModelInfo(BaseModel):
    type: ModelType = Field(description="The type of the model")
    name: str = Field(description="The model name")
    icon: str = Field(description="The icon of the model")
    base_url: str = Field(description="The base URL of the model")
    api_key: str = Field(description="The API key of the model")
    

def get_openai_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            type=ModelType.OPENAI,
            name=model,
            icon="public/openai-fill.svg",
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY
        )
        for model in openai_models
    ]

def get_ollama_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            type=ModelType.OLLAMA,
            name=model,
            icon="public/ollama.svg",
            base_url=OLLAMA_BASE_URL,
            api_key=OLLAMA_API_KEY
        )
        for model in ollama_models
    ]

def get_all_models() -> list[ModelInfo]:
    return get_openai_models() + get_ollama_models()

def get_default_model() -> Union[ModelInfo, None]:
    for model_info in get_all_models():
        if model_info.name == CHAINLIT_CHAT_DEFAULT_MODEL:
            return model_info
    return None

def get_model_info_by_name(name: str | None) -> ModelInfo:
    if name:
        for model_info in get_all_models():
            if model_info.name == name:
                return model_info
    
    default_model = get_default_model()
    if default_model:
        return default_model

    raise ValueError(f"Model `{name}` not found")