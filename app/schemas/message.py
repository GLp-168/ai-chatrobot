"""聊天流程各层共享的消息结构。"""

from typing import Literal, TypedDict


class ChatMessage(TypedDict):
    """一条可发送给 OpenAI 兼容模型的文本消息。"""

    role: Literal["user", "assistant", "system"]
    content: str
