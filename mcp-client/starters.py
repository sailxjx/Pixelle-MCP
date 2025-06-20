from typing import Awaitable, Optional, Callable, Any
import chainlit as cl
from pydantic import BaseModel

ReplyHandler = Callable[[cl.Message], Awaitable[None]]

class StarterModel(BaseModel):
    label: str
    message: str
    icon: Optional[str] = None
    image: Optional[str] = None
    reply_handler: Optional[ReplyHandler] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def to_cl_starter(self) -> cl.Starter:
        """转换为Chainlit Starter对象"""
        return cl.Starter(
            label=self.label,
            message=self.message,
            icon=self.icon,
        )
        
async def handle_old_photo(model: StarterModel):
    await cl.Message(
        content="我已经为你给这张老照片上色，并尽量还原了真实的色彩。请查看生成的彩色版本。",
        elements=[cl.Image(
            size="small",
            url="http://30.150.44.149:9000/files/96d4748b578c49d38318a0e7f7458a59.png"
        )]
    ).send()
    await cl.Message(
        type="user_message",
        content=f"再对上色后的图片生成视频，让图片中的两个人一边笑一边拥抱起来。",
    ).send()
    await cl.Message(
        content=f"我已经根据上色后的图片为你生成了一个视频，内容为图片中的两个人慢慢相视微笑，并逐渐靠近相互拥抱，画面温馨感人。请查看视频效果。",
        elements=[cl.Video(
            size="small",
            url="http://30.150.44.149:9000/files/7a955a69c4074d99a0a5f2852a187855.mp4"
        )]
    ).send()
    
async def handle_multi_modal(model: StarterModel):
    async with cl.Step(name="t2i_by_local_flux") as step:
        step.input = {
            "prompt": "A cute puppy sitting with a playful expression, bright eyes, soft fur, in a warm and cozy indoor setting, photorealistic",
            "width": 512,
            "height": 512
        }
        step.output = "Generated successfully, images: ['http://30.150.44.149:9000/files/4d54d478629141eb8b93b45b1fed021d.png']"
    
    async with cl.Step(name="i2i_by_flux_kontext_pro") as step:
        step.input = {
            "image": "http://30.150.44.149:9000/files/4d54d478629141eb8b93b45b1fed021d.png",
            "prompt": "Add the word 'Pawtist' as a bold title at the top of the image."
        }
        step.output = "Generated successfully, images: ['http://30.150.44.149:9000/files/0f6f15eee9514abf9863fb684691d5c5.png']"
        
    async with cl.Step(name="i2v_by_kling_start_frame") as step:
        step.input = {
            "image": "http://30.150.44.149:9000/files/0f6f15eee9514abf9863fb684691d5c5.png",
            "prompt": "让这只小狗开心地跳跃起来，尾巴摇摆，周围的环境充满活力与欢快的氛围。",
            "model_name": "kling-v1-6",
            "mode": "std"
        }
        step.output = "Generated successfully, videos: ['http://30.150.44.149:9000/files/4b84a9077e7841c69e2fa8bf7be621ba.mp4']"

    async with cl.Step(name="t2s_by_edge_tts") as step:
        step.input = {
            "text": "这是一只活泼可爱的小狗，带着灿烂的笑容跳跃在温馨的室内环境中，展现出无限的欢乐与能量。",
            "voice": "zh-CN-YunxiNeural"
        }
        step.output = "文本转语音成功，音频文件: http://30.150.44.149:9000/files/b1f54c00c11b4a89b9eca4ae11bf560c.mp3"

    await cl.Message(
            content="""我为你完成了以下AIGC创作流程：
1. 生成了一只可爱小狗的图片，并加上了“Pawtist”标题。
2. 根据这张图片制作了小狗跳跃的视频。
3. 生成了一段描述文本，并为其配音。
描述文字：这是一只活泼可爱的小狗，带着灿烂的笑容跳跃在温馨的室内环境中，展现出无限的欢乐与能量。""",
            elements=[
                cl.Image(
                    size="small",
                    url="http://30.150.44.149:9000/files/0f6f15eee9514abf9863fb684691d5c5.png"
                ),
                cl.Audio(
                    size="small",
                    url="http://30.150.44.149:9000/files/b1f54c00c11b4a89b9eca4ae11bf560c.mp3"
                ),
                cl.Video(
                    size="small",
                    url="http://30.150.44.149:9000/files/4b84a9077e7841c69e2fa8bf7be621ba.mp4"
                ),
            ]
        ).send()

DEFAULT_STARTERS = [
    StarterModel(
        label="功能介绍",
        message="你有哪些功能？",
        icon="/public/catalog.svg",
    ),
    StarterModel(
        label="本地ComfyUI推理",
        message="生成一个赛博朋克的城市街道图片，走本地推理",
        icon="/public/flow-compute.svg",
        reply_handler=lambda _: cl.Message(
            content=f"我为你生成了一张赛博朋克风格的城市街道图片，展现了夜晚霓虹灯、未来感市民和高科技氛围。",
            elements=[cl.Image(
                size="large",
                url="http://30.150.44.149:9000/files/c6958285476b486da0e5916864ad801e.png"
            )]
        ).send(),
    ),
    StarterModel(
        label="FLUX Kontext Pro图片编辑",
        message="我要编辑这张图片，让猫的衣服变成红色的，用FLUX模型。",
        icon="/public/replace.svg",
        image="http://30.150.44.149:9000/files/3c134c1de5c54d69b5f3ca59ab4771ad.jpg",
        reply_handler=lambda _: cl.Message(
            content="我已经用FLUX模型编辑了图片，将猫的衣服变成了红色。请查看下方生成的图片。",
            elements=[cl.Image(
                size="medium",
                url="http://30.150.44.149:9000/files/bde97c886ed34dc1a9ccce7c168ea8c1.png"
            )]
        ).send(),
    ),
    StarterModel(
        label="更改图片文字",
        message='把文字改为为"PixelLab MCP"',
        icon="/public/text.svg",
        image="http://30.150.44.149:9000/files/5b4c8282374848cda1f7da3752756f7a.png",
        reply_handler=lambda _: cl.Message(
            content="已经将图片中的文字修改为“PixelLab MCP”。请查看下方生成的图片。",
            elements=[cl.Image(
                size="large",
                url="http://30.150.44.149:9000/files/a0b758ed59c146ebae6a0b7b58cf060e.png"
            )]
        ).send(),
    ),
    StarterModel(
        label="同时更改内容和文字",
        message='青蛙现在是一只老虎，用“PixelLab”代替“ULTRA”，其他文字保留。"',
        icon="/public/text.svg",
        image="http://30.150.44.149:9000/files/761a69e25f574bc3afc48838c7931375.png",
        reply_handler=lambda _: cl.Message(
            content="图片已按你的要求修改：青蛙变成了老虎，并将“ULTRA”替换为“PixelLab”，其他文字保持不变。",
            elements=[cl.Image(
                size="medium",
                url="http://30.150.44.149:9000/files/813d264cafc443e69d7e49c1baa18d8d.png"
            )]
        ).send(),
    ),
    StarterModel(
        label="移除图片中的人物",
        message="移除人物",
        icon="/public/remove-background.svg",
        image="http://30.150.44.149:9000/files/eac6e8ac4b8a475ca10ef6dfbf836971.png",
        reply_handler=lambda _: cl.Message(
            content="已为你移除图片中的人物，请查看下方新处理的图片。",
            elements=[cl.Image(
                size="large",
                url="http://30.150.44.149:9000/files/e76bc0ce93df4de9b305da883244933d.png"
            )]
        ).send(),
    ),
    StarterModel(
        label="局部替换图片内容",
        message="给杯子毛绒的手臂、腿和简单的脸，杯子的主体不变，让他开心的微笑。",
        icon="/public/replace.svg",
        image="http://30.150.44.149:9000/files/2e99efc5f5f14d8791fca740d01b4077.jpg",
        reply_handler=lambda _: cl.Message(
            content="已为你的杯子添加了毛绒手臂、腿和一张简单开心的笑脸，并保持了杯子的主体不变。请查看效果：",
            elements=[cl.Image(
                size="small",
                url="http://30.150.44.149:9000/files/79f1db3e303040e094243aeb35b08852.png"
            )]
        ).send(),
    ),
    StarterModel(
        label="GPT4图片编辑",
        message="我要编辑这张图片，让猫的衣服变成红色的，用GPT4模型。",
        icon="/public/replace.svg",
        image="http://30.150.44.149:9000/files/3c134c1de5c54d69b5f3ca59ab4771ad.jpg",
        reply_handler=lambda _: cl.Message(
            content="我已经用GPT4模型编辑了图片，将猫的衣服变成了红色。请查看下方生成的图片。",
            elements=[cl.Image(
                size="small",
                url="http://30.150.44.149:9000/files/a388865e6d8a4b32b5aa29a1cdf0fbe2.png"
            )]
        ).send(),
    ),
    StarterModel(
        label="老照片修复",
        message="给这张老照片上色",
        icon="/public/video.svg",
        image="http://30.150.44.149:9000/files/9b21af9cf583477e8af3b42dcadd2fa0.png",
        reply_handler=handle_old_photo,
    ),
    StarterModel(
        label="图片转视频",
        message="让图片里的人物摸了摸下巴，然后突然笑起来",
        icon="/public/video.svg",
        image="http://30.150.44.149:9000/files/7529378fc78347c4bc307b9eeb12a0c0.png",
        reply_handler=lambda _: cl.Message(
            content="视频已生成，内容为图片中的人物先轻轻摸了摸下巴，然后突然露出灿烂的笑容。您可以点击下方视频进行查看。",
            elements=[cl.Video(
                size="small",
                url="http://30.150.44.149:9000/files/2fe27d90a36e46dc815b27d7c758c3c0.mp4"
            )]
        ).send(),
    ),
    StarterModel(
        label="TTS文本转音频",
        message="写一首关于生命的意义的短视频脚本，然后转音频。",
        icon="/public/sound.svg",
        reply_handler=lambda _: cl.Message(
            content="""短视频脚本如下：
每个人都曾思考过一个问题：生命的意义究竟是什么？
有人说，生命是奋斗，是一次次挑战极限后的成长。
有人说，生命是陪伴，是和家人朋友共度的温暖时光。
也有人说，生命是体验，是在悲欢离合中感受真实的自己。
也许，生命的意义并没有统一的答案。
重要的是，我们在有限的时光里，用心去爱、去追寻、去尝试。
生命如诗，每个人都能写出属于自己的篇章。
我已为你将这段文字转化为音频，方便用于短视频配音。""",
            elements=[cl.Audio(
                size="small",
                url="http://30.150.44.149:9000/files/f7beedfcff2f44e5925fe2ff1882dd47.mp3"
            )]
        ).send(),
    ),
    StarterModel(
        label="多模态复杂链路生成",
        message='生成一个小狗的图片，然后再给图片加上"Pawtist"的标题，然后再做一个让这个小狗跳跃的视频，然后再生成一段描述文字，并转语音',
        icon="/public/video.svg",
        reply_handler=handle_multi_modal,
    ),
]


@cl.set_starters
async def set_starters():
    return [starter.to_cl_starter() for starter in DEFAULT_STARTERS]

async def hook_by_starters(message: cl.Message):
    """Hook函数：根据starter消息内容进行处理"""
    
    # 检查是否为首条用户消息
    cl_messages = cl.chat_context.get()
    user_messages = [msg for msg in cl_messages if msg.type == "user_message"]
    is_first_message = len(user_messages) == 1
    if not is_first_message:
        return False
    
    # 严格匹配消息内容
    for starter in DEFAULT_STARTERS:
        if message.content != starter.message:
            continue
        if starter.image and not message.elements:
            message.elements.append(cl.Image(
                size="small",
                url=starter.image
            ))
            await message.update()
        if starter.reply_handler:
            await starter.reply_handler(starter)
            return True
    
    return False