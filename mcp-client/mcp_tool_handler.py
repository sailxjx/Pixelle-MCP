from datetime import timedelta
import json
import time
from venv import logger
import chainlit as cl
from typing import Any, Dict, List
from openai import AsyncOpenAI
from mcp import ClientSession
import re
from httpx import Timeout
from time_util import format_duration

# 严格的媒体显示系统指令
SYSTEM_INSTRUCTION = """
# 关于媒体显示的说明
当工具返回包含媒体文件的结果时，如果媒体文件是用户想要看到的最终结果，请严格按照以下格式在回复的最后添加媒体标记：

格式要求：
1. 先完成你的正常文字回复
2. 如果有需要显示的媒体文件，在文字回复结束后换行
3. 每个媒体文件单独一行，格式为：
   - 图片：[SHOW_IMAGE:图片URL或路径]
   - 音频：[SHOW_AUDIO:音频URL或路径]
   - 视频：[SHOW_VIDEO:视频URL或路径]
4. 可以是网络URL或本地文件路径

示例：
我为你生成了销售数据分析图表和相关的讲解音频。从数据可以看出销量呈上升趋势，特别是在第三季度有显著增长。

[SHOW_IMAGE:http://example.com/sales_chart.png]
[SHOW_AUDIO:http://example.com/sales_explanation.mp3]

如果还包含了视频演示：
[SHOW_VIDEO:http://example.com/sales_demo.mp4]

注意：
- 只为最终的、用户需要查看的结果媒体文件添加此标记
- 不要为中间处理步骤的媒体文件添加标记
- 媒体标记必须放在回复的最后
- 每个媒体标记单独一行
- 支持的媒体类型：图片(IMAGE)、音频(AUDIO)、视频(VIDEO)
"""

def get_all_tools() -> List[Dict[str, Any]]:
    """获取所有可用的 MCP 工具"""
    mcp_tools = cl.user_session.get("mcp_tools", {})
    all_tools = []
    for connection_tools in mcp_tools.values():
        all_tools.extend(connection_tools)
    return all_tools


def find_tool_connection(tool_name: str) -> str:
    """查找工具所属的 MCP 连接"""
    mcp_tools = cl.user_session.get("mcp_tools", {})
    for connection_name, tools in mcp_tools.items():
        if any(tool["function"]["name"] == tool_name for tool in tools):
            return connection_name
    return None


def _extract_content(content_list):
    """从 CallToolResult 的 content 列表中提取文本内容"""
    if not content_list:
        return ""
    
    text_parts = []
    for content_item in content_list:
        # 处理不同类型的内容
        if hasattr(content_item, 'text'):
            # TextContent
            text_parts.append(content_item.text)
        elif hasattr(content_item, 'data'):
            # ImageContent 或其他二进制内容
            text_parts.append(f"[Binary content: {getattr(content_item, 'mimeType', 'unknown')}]")
        elif hasattr(content_item, 'uri'):
            # EmbeddedResource
            text_parts.append(f"[Resource: {content_item.uri}]")
        else:
            # 其他未知类型，尝试转换为字符串
            text_parts.append(str(content_item))
    
    return text_parts[0] if len(text_parts) == 1 else text_parts


@cl.step(type="tool")
async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """执行 MCP 工具调用"""
    # 记录开始时间
    start_time = time.time()
    
    def _format_result_with_duration(content: str) -> str:
        """统一格式化带耗时的结果"""
        duration = time.time() - start_time
        return f"[耗时{format_duration(duration)}] {content}"
    
    current_step = cl.context.current_step
    current_step.input = tool_input
    current_step.name = tool_name
    await current_step.update()
    
    # 查找工具所属的连接
    mcp_name = find_tool_connection(tool_name)
    if not mcp_name:
        error_msg = json.dumps({"error": f"Tool {tool_name} not found in any MCP connection"})
        result_with_duration = _format_result_with_duration(error_msg)
        current_step.output = result_with_duration
        return result_with_duration
    
    # 获取 MCP 会话
    mcp_session, _ = cl.context.session.mcp_sessions.get(mcp_name)
    if not mcp_session:
        error_msg = json.dumps({"error": f"MCP {mcp_name} not found in any MCP connection"})
        result_with_duration = _format_result_with_duration(error_msg)
        current_step.output = result_with_duration
        return result_with_duration
    
    try:
        # 调用 MCP 工具，返回 CallToolResult 对象
        logger.info(f"Calling MCP tool: {tool_name} with input: {tool_input}")
        result = await mcp_session.call_tool(tool_name, tool_input, read_timeout_seconds=timedelta(hours=1))
        
        # 检查是否有错误
        if result.isError:
            error_content = _extract_content(result.content)
            logger.error(f"Tool execution failed: {error_content}")
            error_msg = json.dumps({"error": f"Tool execution failed: {error_content}"})
            result_with_duration = _format_result_with_duration(error_msg)
            current_step.output = result_with_duration
            return result_with_duration
        
        # 提取内容文本
        content = _extract_content(result.content)
        logger.info(f"Tool execution succeeded: {content}")
        result_with_duration = _format_result_with_duration(str(content))
        current_step.output = result_with_duration
        return result_with_duration
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        error_msg = json.dumps({"error": str(e)})
        result_with_duration = _format_result_with_duration(error_msg)
        current_step.output = result_with_duration
        return result_with_duration


def _inject_system_instruction(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """注入媒体显示的系统指令"""
    messages_copy = messages.copy()
    
    if messages_copy and messages_copy[0]["role"] == "system":
        # 检查是否已经包含完整的媒体显示指令，避免重复添加
        if SYSTEM_INSTRUCTION not in messages_copy[0]["content"]:
            messages_copy[0]["content"] += "\n\n" + SYSTEM_INSTRUCTION
    else:
        # 如果没有系统消息，插入新的系统消息
        messages_copy.insert(0, {"role": "system", "content": SYSTEM_INSTRUCTION})
    
    return messages_copy


def _extract_and_clean_media_markers(text: str) -> tuple[Dict[str, List[str]], str]:
    """提取媒体标记并清理文本
    
    Returns:
        tuple: (媒体文件字典, 清理后的文本)
               媒体文件字典格式: {"images": [...], "audios": [...], "videos": [...]}
    """
    # 匹配不同类型的媒体标记
    patterns = {
        "images": r'\n\[SHOW_IMAGE:([^\]]+)\]',
        "audios": r'\n\[SHOW_AUDIO:([^\]]+)\]',
        "videos": r'\n\[SHOW_VIDEO:([^\]]+)\]'
    }
    
    media_files = {"images": [], "audios": [], "videos": []}
    cleaned_text = text
    
    # 提取各类型媒体文件并清理文本
    for media_type, pattern in patterns.items():
        media_files[media_type] = re.findall(pattern, cleaned_text)
        cleaned_text = re.sub(pattern, '', cleaned_text)
    
    # 移除多余的空白字符
    cleaned_text = cleaned_text.rstrip()
    
    return media_files, cleaned_text


def _is_url(source: str) -> bool:
    """判断媒体源是否为URL"""
    return source.startswith(('http://', 'https://'))


async def _process_media_markers(msg: cl.Message):
    """处理消息中的媒体标记"""
    if not msg.content:
        return
        
    # 提取媒体标记并清理文本
    media_files, cleaned_content = _extract_and_clean_media_markers(msg.content)
    
    # 更新消息内容（移除标记）
    msg.content = cleaned_content
    
    # 处理图片
    for i, img_source in enumerate(media_files["images"]):
        img_source = img_source.strip()
        
        img_params = {
            "name": f"Generated_Image_{i+1}",
            "display": "inline",
            "size": "small",
        }
        
        if _is_url(img_source):
            img_params["url"] = img_source
        else:
            img_params["path"] = img_source
        
        img_element = cl.Image(**img_params)
        msg.elements.append(img_element)
        logger.info(f"Added image element: {img_source}")
    
    # 处理音频
    for i, audio_source in enumerate(media_files["audios"]):
        audio_source = audio_source.strip()
        
        audio_params = {
            "name": f"Generated_Audio_{i+1}",
            "display": "inline",
            "size": "small",
        }
        
        if _is_url(audio_source):
            audio_params["url"] = audio_source
        else:
            audio_params["path"] = audio_source
        
        audio_element = cl.Audio(**audio_params)
        msg.elements.append(audio_element)
        logger.info(f"Added audio element: {audio_source}")
    
    # 处理视频
    for i, video_source in enumerate(media_files["videos"]):
        video_source = video_source.strip()
        
        video_params = {
            "name": f"Generated_Video_{i+1}",
            "display": "inline",
            "size": "small",
        }
        
        if _is_url(video_source):
            video_params["url"] = video_source
        else:
            video_params["path"] = video_source
        
        video_element = cl.Video(**video_params)
        msg.elements.append(video_element)
        logger.info(f"Added video element: {video_source}")


async def _process_tool_call_delta(
    tool_calls_delta: List[Any], 
    current_tool_calls: Dict[int, Dict], 
    current_args: Dict[int, str]
):
    """处理工具调用的增量数据"""
    for tool_call_delta in tool_calls_delta:
        index = tool_call_delta.index
        
        # 初始化工具调用数据结构
        if index not in current_tool_calls:
            current_tool_calls[index] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""}
            }
            current_args[index] = ""
        
        # 累积工具调用信息
        if tool_call_delta.id:
            current_tool_calls[index]["id"] = tool_call_delta.id
        if tool_call_delta.function and tool_call_delta.function.name:
            current_tool_calls[index]["function"]["name"] = tool_call_delta.function.name
        if tool_call_delta.function and tool_call_delta.function.arguments:
            current_args[index] += tool_call_delta.function.arguments
            current_tool_calls[index]["function"]["arguments"] = current_args[index]


async def _execute_tool_calls(
    current_tool_calls: Dict[int, Dict], 
    messages: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """执行所有工具调用并更新消息历史"""
    # 构建包含工具调用的助手消息
    tool_calls_list = list(current_tool_calls.values())
    messages.append({
        "role": "assistant",
        "content": None,
        "tool_calls": tool_calls_list
    })
    
    # 执行所有工具调用
    for tool_call in tool_calls_list:
        tool_name = tool_call["function"]["name"]
        tool_args_str = tool_call["function"]["arguments"]
        
        try:
            # 解析工具参数
            tool_args = json.loads(tool_args_str)
            
            # 执行工具调用
            tool_response = await execute_tool(tool_name, tool_args)
            
            # 添加工具响应到消息历史
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": tool_response
            })
            
        except Exception as e:
            error_message = f"工具调用错误: {str(e)}"
            logger.error(error_message)
            # 添加错误响应到消息历史
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": error_message
            })
    
    return messages


async def _handle_stream_chunk(chunk, msg, current_tool_calls, current_args):
    """处理流式响应的单个chunk"""
    choice = chunk.choices[0]
    delta = choice.delta
    has_tool_call = False
    
    # 处理工具调用
    if delta.tool_calls:
        has_tool_call = True
        await _process_tool_call_delta(
            delta.tool_calls, 
            current_tool_calls, 
            current_args
        )
    
    # 处理普通文本响应
    elif delta.content:
        await msg.stream_token(delta.content)
    
    return has_tool_call, choice.finish_reason


async def _handle_stream_response(client, api_params, msg, enhanced_messages, messages):
    """处理单次流式响应"""
    current_tool_calls = {}
    current_args = {}
    has_tool_call = False
    
    try:
        response = await client.chat.completions.create(**api_params)
        
        try:
            async for chunk in response:
                chunk_has_tool_call, finish_reason = await _handle_stream_chunk(
                    chunk, msg, current_tool_calls, current_args
                )
                
                if chunk_has_tool_call:
                    has_tool_call = True
                
                # 检查完成状态
                if finish_reason == 'tool_calls':
                    try:
                        # 执行工具调用
                        enhanced_messages = await _execute_tool_calls(
                            current_tool_calls, 
                            enhanced_messages
                        )
                        return enhanced_messages, True  # 继续下一轮
                        
                    except Exception as e:
                        error_message = f"处理工具调用时发生错误: {str(e)}"
                        logger.error(error_message)
                        await msg.stream_token(f"\n{error_message}\n")
                        return messages, False  # 结束处理
                
                elif finish_reason:  # 其他完成原因
                    if not has_tool_call:
                        # 处理媒体标记
                        await _process_media_markers(msg)
                        return messages, False  # 结束处理
                        
        except GeneratorExit:
            logger.debug("Stream generator closed gracefully")
        except Exception as e:
            logger.error(f"Stream iteration error: {e}")
        finally:
            # 显式关闭响应流以确保资源正确释放
            if hasattr(response, 'close'):
                try:
                    await response.close()
                except Exception as close_error:
                    logger.debug(f"Error closing response stream: {close_error}")
                    
    except Exception as api_error:
        logger.error(f"API request error: {api_error}")
    
    # 如果没有工具调用，结束循环
    if not has_tool_call:
        await _process_media_markers(msg)
        return messages, False
    
    return enhanced_messages, True


async def process_streaming_response(
    messages: List[Dict[str, Any]], 
    msg: cl.Message,
    model: str,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    处理流式响应和工具调用
    
    Args:
        messages: 消息历史
        msg: Chainlit 消息对象
        model: 使用的模型名称
        **kwargs: 其他 OpenAI API 参数
        
    Returns:
        更新后的消息历史
    """
    tools = get_all_tools()
    
    # 注入媒体显示系统指令
    enhanced_messages = _inject_system_instruction(messages)
    
    while True:  # 循环处理工具调用
        # 准备 API 参数
        api_params = {
            "model": model,
            "messages": enhanced_messages,
            "stream": True,
            **kwargs
        }
        
        # 如果有工具，添加工具参数
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = "auto"
        
        client = AsyncOpenAI(timeout=Timeout(None))
        
        try:
            enhanced_messages, should_continue = await _handle_stream_response(
                client, api_params, msg, enhanced_messages, messages
            )
            
            if not should_continue:
                return enhanced_messages
                
        finally:
            # 显式关闭客户端以避免异步上下文冲突
            try:
                await client.close()
            except Exception as client_close_error:
                logger.debug(f"Error closing OpenAI client: {client_close_error}")


# MCP 连接管理的便捷函数
async def handle_mcp_connect(connection, session: ClientSession, tools_converter_func):
    """处理 MCP 连接的通用逻辑"""
    tools_result = await session.list_tools()
    openai_tools = tools_converter_func(tools_result.tools)
    
    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_tools[connection.name] = openai_tools
    cl.user_session.set("mcp_tools", mcp_tools)

async def handle_mcp_disconnect(name: str):
    """处理 MCP 断开连接的通用逻辑"""
    mcp_tools = cl.user_session.get("mcp_tools", {})
    if name in mcp_tools:
        del mcp_tools[name]
    cl.user_session.set("mcp_tools", mcp_tools) 