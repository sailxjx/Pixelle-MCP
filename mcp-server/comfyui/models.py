# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ExecuteResult(BaseModel):
    """执行结果模型"""
    status: str = Field(description="执行状态")
    prompt_id: Optional[str] = Field(None, description="提示ID")
    duration: Optional[float] = Field(None, description="执行耗时（秒）")
    images: List[str] = Field(default_factory=list, description="图片URL列表")
    images_by_var: Dict[str, List[str]] = Field(default_factory=dict, description="按变量名分组的图片")
    audios: List[str] = Field(default_factory=list, description="音频URL列表")
    audios_by_var: Dict[str, List[str]] = Field(default_factory=dict, description="按变量名分组的音频")
    videos: List[str] = Field(default_factory=list, description="视频URL列表")
    videos_by_var: Dict[str, List[str]] = Field(default_factory=dict, description="按变量名分组的视频")
    texts: List[str] = Field(default_factory=list, description="文本列表")
    texts_by_var: Dict[str, List[str]] = Field(default_factory=dict, description="按变量名分组的文本")
    outputs: Optional[Dict[str, Any]] = Field(None, description="原始输出")
    msg: Optional[str] = Field(None, description="消息")
    
    def to_llm_result(self) -> str:
        """转换为LLM可读的结果"""
        if self.status == "completed":
            output = "Generated successfully"
            
            def format_media_output(media_type: str, media_list: List[str], by_var_dict: Dict[str, List[str]]) -> str:
                """格式化媒体输出"""
                if by_var_dict and len(by_var_dict) > 1:
                    var_dict = {k: v[0] if v else None for k, v in by_var_dict.items()}
                    return f", {media_type}: {var_dict}"
                else:
                    return f", {media_type}: {media_list}"
            
            # 处理各种媒体类型
            for media_type in ["images", "audios", "videos", "texts"]:
                media_list = getattr(self, media_type)
                by_var_dict = getattr(self, f"{media_type}_by_var")
                if media_list:
                    output += format_media_output(media_type, media_list, by_var_dict)
            
            return output
        else:
            result = f"Generated failed, status: {self.status}"
            if self.msg:
                result += f", message: {self.msg}"
            return result 