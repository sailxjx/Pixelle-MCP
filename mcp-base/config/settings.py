"""
基础服务配置管理
支持多种存储后端的配置
"""

from enum import Enum
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class StorageType(str, Enum):
    """存储类型枚举"""
    LOCAL = "local"
    MINIO = "minio"
    # 未来可扩展: OSS = "oss", COS = "cos"


class Settings(BaseSettings):
    """基础服务配置"""
    
    # 服务基础配置
    app_name: str = "Pixelle Base Service"
    app_version: str = "0.1.0"
    host: str = "localhost"
    port: int = 9001
    debug: bool = False
    
    # 存储配置
    storage_type: StorageType = StorageType.LOCAL
    
    # 本地存储配置
    local_storage_path: str = "data/files"
    
    # MinIO配置（当storage_type=minio时使用）
    minio_endpoint: Optional[str] = "localhost:9000"
    minio_access_key: Optional[str] = "minio"
    minio_secret_key: Optional[str] = "minio1234"
    minio_bucket: Optional[str] = "files"
    minio_secure: bool = False
    
    # 文件配置
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: list[str] = [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",  # 图片
        ".mp4", ".avi", ".mov", ".mkv", ".webm",  # 视频
        ".mp3", ".wav", ".flac", ".aac", ".ogg",  # 音频
        ".txt", ".json", ".csv", ".pdf"  # 文档
    ]
    
    # API配置
    cors_origins: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings() 