import asyncio
import io
import tempfile
import os
from typing import Optional, Literal
from pydantic import BaseModel, Field
import edge_tts
from core import logger
from utils.file_uploader import upload


class TtsResult(BaseModel):
    """TTS转换结果"""
    success: bool = Field(description="转换是否成功")
    audio_url: Optional[str] = Field(None, description="音频文件URL")
    error: Optional[str] = Field(None, description="错误信息")
    
    def to_llm_result(self) -> str:
        if self.success:
            return f"文本转语音成功，音频文件: {self.audio_url}"
        else:
            return f"文本转语音失败，错误信息: {self.error}"


async def text_to_speech_async(
    text: str,
    voice: str = "zh-CN-YunxiNeural",
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz"
) -> TtsResult:
    """
    异步将文本转换为语音
    
    Args:
        text: 要转换的文本
        voice: 语音名称，默认为zh-CN-YunxiNeural
        rate: 语速调整，例如: "+50%", "-20%", "+0%"
        volume: 音量调整，例如: "+50%", "-20%", "+0%"
        pitch: 音调调整，例如: "+50Hz", "-20Hz", "+0Hz"
    
    Returns:
        TtsResult: 转换结果
    """
    try:
        logger.info(f"开始文本转语音: text={text[:50]}..., voice={voice}")
        
        # 创建TTS通信对象
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # 保存音频到临时文件
            await communicate.save(temp_path)
            
            # 上传到存储服务
            audio_url = upload(temp_path)
            
            logger.info(f"文本转语音成功，音频URL: {audio_url}")
            return TtsResult(success=True, audio_url=audio_url)
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        logger.error(f"文本转语音失败: {e}", exc_info=True)
        return TtsResult(success=False, error=str(e))


async def text_to_speech(
    text: str,
    voice: str = "zh-CN-YunxiNeural",
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz"
) -> TtsResult:
    """
    同步将文本转换为语音（包装异步方法）
    
    Args:
        text: 要转换的文本
        voice: 语音名称，默认为zh-CN-YunxiNeural
        rate: 语速调整，例如: "+50%", "-20%", "+0%"
        volume: 音量调整，例如: "+50%", "-20%", "+0%"
        pitch: 音调调整，例如: "+50Hz", "-20Hz", "+0Hz"
    
    Returns:
        TtsResult: 转换结果
    """
    return await text_to_speech_async(text, voice, rate, volume, pitch)


async def list_voices() -> list[dict]:
    """
    异步获取所有可用的语音列表
    
    Returns:
        list[dict]: 语音列表，每个元素包含Name, Gender, ContentCategories等信息
    """
    try:
        voices = await edge_tts.list_voices()
        return voices
    except Exception as e:
        logger.error(f"获取语音列表失败: {e}", exc_info=True)
        return []


async def get_chinese_voices() -> list[dict]:
    """
    获取中文语音列表
    
    Returns:
        list[dict]: 中文语音列表
    """
    all_voices = await list_voices()
    chinese_voices = [
        voice for voice in all_voices 
        if voice.get('ShortName', '').startswith('zh-')
    ]
    return chinese_voices


if __name__ == "__main__":
    # 测试文本转语音功能
    test_text = "你好，这是一个基于edge-tts开源库的文本转语音测试。"
    
    print("开始测试文本转语音功能...")
    result = asyncio.run(text_to_speech(
        text=test_text,
        voice="zh-CN-YunjianNeural"
    ))
    
    print(f"转换结果: {result.to_llm_result()}")
    print(f"详细信息: {result.model_dump_json(indent=2)}") 