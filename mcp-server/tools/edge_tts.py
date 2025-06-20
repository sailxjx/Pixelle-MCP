from typing import Optional, Literal
from pydantic import Field
from core import mcp_tool
from utils.edge_tts_util import text_to_speech, get_chinese_voices


@mcp_tool
async def t2s_by_edge_tts(
    text: str = Field(description="要转换为语音的文本内容"),
    voice: str = Field(
        "zh-CN-YunxiNeural", 
        description="语音名称，支持中文语音如：zh-CN-YunxiNeural（男声）、zh-CN-YunjianNeural（男声）、zh-CN-XiaoxiaoNeural（女声）、zh-CN-XiaoyiNeural（女声）等"
    ),
    rate: str = Field(
        "+0%", 
        description="语速调整，格式如：+50%（加速50%）、-20%（减速20%）、+0%（正常语速）"
    ),
):
    """
    使用Edge TTS开源库将文本转换为语音。
    
    这是一个基于edge-tts开源项目的文本转语音工具，无需API密钥，
    支持多种中文语音和语音参数调整。
    
    功能特性：
    - 支持多种中文语音（男声、女声）
    - 可调整语速
    - 高质量语音合成
    - 免费使用，无需API密钥
    
    使用示例：
    - 基本用法：text="你好，欢迎使用语音合成服务"
    - 女声合成：voice="zh-CN-XiaoxiaoNeural"
    - 快速语音：rate="+50%"
    
    支持的中文语音包括：
    - zh-CN-YunxiNeural（男声，默认）
    - zh-CN-YunjianNeural（男声）
    - zh-CN-XiaoxiaoNeural（女声）
    - zh-CN-XiaoyiNeural（女声）
    - 更多语音请参考 list_chinese_voices 工具
    
    注意事项：
    - 文本长度建议控制在1000字符以内
    - 语速调整范围：-50%到+100%
    """
    result = await text_to_speech(
        text=text,
        voice=voice,
        rate=rate,
        volume="+0%",  # 固定为正常音量
        pitch="+0Hz"   # 固定为正常音调
    )
    return result.to_llm_result()


@mcp_tool
async def list_chinese_voices():
    """
    获取所有可用的中文语音列表。
    
    返回支持的中文语音信息，包括语音名称、性别、地区等详细信息。
    可以用于了解当前可用的语音选项。
    
    返回信息包括：
    - Name: 语音名称（用于voice参数）
    - Gender: 性别（Male/Female）
    - Locale: 地区代码
    - ContentCategories: 内容分类
    - VoicePersonalities: 语音特性
    """
    try:
        voices = await get_chinese_voices()
        if not voices:
            return "获取语音列表失败，请检查网络连接。"
        
        result = f"找到 {len(voices)} 个中文语音：\n\n"
        
        for voice in voices:
            name = voice.get('Name', '')
            gender = voice.get('Gender', '')
            locale = voice.get('Locale', '')
            personalities = voice.get('VoicePersonalities', [])
            
            result += f"• {name}\n"
            result += f"  性别: {gender}\n"
            result += f"  地区: {locale}\n"
            if personalities:
                result += f"  特性: {', '.join(personalities)}\n"
            result += "\n"
        
        result += "使用示例：\n"
        result += f"t2s_by_edge_tts_v2(text='你好世界', voice='{voices[0].get('Name')}')"
        
        return result
        
    except Exception as e:
        return f"获取语音列表时发生错误：{str(e)}" 