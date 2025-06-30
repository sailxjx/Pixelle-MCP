from typing import Awaitable, Optional, Callable, Any, List, Dict, Tuple
import chainlit as cl
from pydantic import BaseModel
import json
from pathlib import Path
import re

ReplyHandler = Callable[[cl.Message], Awaitable[None]]

class StarterModel(BaseModel):
    label: str
    message: str
    icon: Optional[str] = None
    image: Optional[str] = None
    reply_handler: Optional[ReplyHandler] = None
    preset_response: Optional[List[Dict[str, Any]]] = None
    enabled: bool = True
    order: int = 999
    
    class Config:
        arbitrary_types_allowed = True
    
    def to_cl_starter(self) -> cl.Starter:
        """转换为Chainlit Starter对象"""
        return cl.Starter(
            label=self.label,
            message=self.message,
            icon=self.icon,
        )

# 文件操作相关函数
STARTERS_DIR = Path("./data/starters")

def ensure_starters_dir():
    """确保 starters 目录存在"""
    STARTERS_DIR.mkdir(parents=True, exist_ok=True)

def parse_filename(filename: str) -> Tuple[bool, int, str]:
    """
    解析文件名格式：[_]xxx_label.json
    返回：(enabled, order, label)
    """
    # 移除.json后缀
    name = filename.replace('.json', '')
    
    # 检查是否以_开头（禁用标记）
    enabled = True
    if name.startswith('_'):
        enabled = False
        name = name[1:]  # 移除前面的_
    
    # 匹配格式：xxx_label
    match = re.match(r'^(\d+)_(.+)$', name)
    if match:
        order = int(match.group(1))
        label = match.group(2)
        return enabled, order, label
    else:
        # 如果不匹配格式，返回默认值
        return enabled, 999, name

def load_custom_starter(starter_file: Path) -> Optional[StarterModel]:
    """从文件加载单个自定义 starter"""
    try:
        # 解析文件名
        enabled, order, expected_label = parse_filename(starter_file.name)
        
        with open(starter_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return StarterModel(
            label=data.get("label", expected_label),
            message=data.get("message", ""),
            icon=data.get("icon", "/public/text.svg"),
            image=data.get("image", None),
            preset_response=data.get("preset_response", None),
            enabled=enabled,
            order=order,
        )
    except Exception as e:
        print(f"Error loading starter from {starter_file}: {e}")
        return None

def load_custom_starters() -> List[StarterModel]:
    """加载所有自定义 starters，按文件名排序"""
    ensure_starters_dir()
    custom_starters = []
    
    for starter_file in STARTERS_DIR.glob("*.json"):
        starter = load_custom_starter(starter_file)
        if starter and starter.enabled:  # 只加载启用的starters
            custom_starters.append(starter)
    
    # 按order字段排序
    custom_starters.sort(key=lambda x: x.order)
    
    return custom_starters

def get_all_starters() -> List[StarterModel]:
    """获取所有启用的 starters，按文件名顺序排列"""
    return load_custom_starters()

async def handle_preset_response(preset_response: List[Dict[str, Any]]) -> None:
    """处理预置回答数组"""
    if not preset_response:
        return
    
    for item in preset_response:
        role = item.get("role", "ai")
        item_type = item.get("type", "message")
        
        if item_type == "step":
            await handle_step_item(item)
        elif item_type == "message":
            await handle_message_item(item, role)

async def handle_step_item(item: Dict[str, Any]) -> None:
    """处理步骤项"""
    step_name = item.get("name", "处理中...")
    step_input = item.get("input", {})
    step_output = item.get("output", "")
    
    async with cl.Step(name=step_name) as step:
        step.input = step_input
        step.output = step_output

async def handle_message_item(item: Dict[str, Any], role: str) -> None:
    """处理消息项"""
    content = item.get("content", "")
    elements_data = item.get("elements", [])
    
    # 构建元素列表
    elements = []
    for elem_data in elements_data:
        elem_type = elem_data.get("type", "")
        elem_url = elem_data.get("url", "")
        elem_size = elem_data.get("size", "small")
        
        if elem_type == "image" and elem_url:
            elements.append(cl.Image(url=elem_url, size=elem_size))
        elif elem_type == "video" and elem_url:
            elements.append(cl.Video(url=elem_url, size=elem_size))
        elif elem_type == "audio" and elem_url:
            elements.append(cl.Audio(url=elem_url, size=elem_size))
    
    # 根据角色发送不同类型的消息
    if role == "user":
        # 用户消息
        message = cl.Message(
            type="user_message", 
            content=content, 
            elements=elements
        )
    else:
        # AI助手消息
        message = cl.Message(
            content=content, 
            elements=elements
        )
    
    await message.send()

@cl.set_starters
async def set_starters():
    return [starter.to_cl_starter() for starter in get_all_starters()]

async def hook_by_starters(message: cl.Message):
    """Hook函数：根据starter消息内容进行处理"""
    
    # 检查是否为首条用户消息
    cl_messages = cl.chat_context.get()
    user_messages = [msg for msg in cl_messages if msg.type == "user_message"]
    is_first_message = len(user_messages) == 1
    if not is_first_message:
        return False
    
    # 严格匹配消息内容
    for starter in get_all_starters():
        if message.content != starter.message:
            continue
        if starter.image and not message.elements:
            message.elements.append(cl.Image(
                size="small",
                url=starter.image
            ))
            await message.update()
        
        # 优先使用预置回答
        if starter.preset_response:
            await handle_preset_response(starter.preset_response)
            return True
        # 其次使用传统的 reply_handler
        elif starter.reply_handler:
            await starter.reply_handler(starter)
            return True
    
    return False