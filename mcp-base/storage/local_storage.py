"""
本地文件存储实现
将文件存储到本地文件系统
"""

import os
import uuid
import aiofiles
from pathlib import Path
from typing import BinaryIO, Optional

from .base import StorageBackend, FileInfo
from config.settings import settings


class LocalStorage(StorageBackend):
    """本地文件存储"""
    
    def __init__(self, storage_path: Optional[str] = None, base_url: Optional[str] = None):
        self.storage_path = Path(storage_path or settings.local_storage_path)
        self.base_url = base_url or f"http://{settings.host}:{settings.port}"
        
        # 确保存储目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _generate_file_id(self, filename: str) -> str:
        """生成唯一的文件ID"""
        # 保留文件扩展名
        ext = Path(filename).suffix
        return f"{uuid.uuid4().hex}{ext}"
    
    def _get_file_path(self, file_id: str) -> Path:
        """获取文件的完整路径"""
        return self.storage_path / file_id
    
    def _get_file_url(self, file_id: str) -> str:
        """获取文件的访问URL"""
        return f"{self.base_url}/files/{file_id}"
    
    async def upload(
        self, 
        file_data: BinaryIO, 
        filename: str, 
        content_type: str
    ) -> FileInfo:
        """上传文件到本地存储"""
        # 生成唯一文件ID
        file_id = self._generate_file_id(filename)
        file_path = self._get_file_path(file_id)
        
        # 异步写入文件
        async with aiofiles.open(file_path, 'wb') as f:
            content = file_data.read()
            await f.write(content)
        
        # 获取文件大小
        file_size = len(content)
        
        return FileInfo(
            file_id=file_id,
            filename=filename,
            content_type=content_type,
            size=file_size,
            url=self._get_file_url(file_id)
        )
    
    async def download(self, file_id: str) -> Optional[bytes]:
        """从本地存储下载文件"""
        file_path = self._get_file_path(file_id)
        
        if not file_path.exists():
            return None
        
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
        except Exception:
            return None
    
    async def delete(self, file_id: str) -> bool:
        """删除本地文件"""
        file_path = self._get_file_path(file_id)
        
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    async def exists(self, file_id: str) -> bool:
        """检查本地文件是否存在"""
        file_path = self._get_file_path(file_id)
        return file_path.exists()
    
    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """获取本地文件信息"""
        file_path = self._get_file_path(file_id)
        
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            # 从文件名推断内容类型
            import mimetypes
            content_type, _ = mimetypes.guess_type(str(file_path))
            
            return FileInfo(
                file_id=file_id,
                filename=file_path.name,
                content_type=content_type or "application/octet-stream",
                size=stat.st_size,
                url=self._get_file_url(file_id)
            )
        except Exception:
            return None 