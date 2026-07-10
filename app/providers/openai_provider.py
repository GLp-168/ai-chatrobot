"""OpenAI 兼容大模型的访问适配器。"""

from openai import OpenAI

from app.core.setting import Settings
from app.schemas.message import ChatMessage


class OpenAIProvider:
    """把应用内部的聊天消息转换为一次 OpenAI 兼容 API 调用。"""

    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=Settings.OPENAI_API_KEY,
            base_url=Settings.OPENAI_BASE_URL,
        )

    def chat(self, messages: list[ChatMessage]) -> str:
        """将完整对话上下文发送给模型并返回纯文本回复。"""
        response = self.client.chat.completions.create(
            model=Settings.MODEL_NAME,
            messages=messages,
        )

        return response.choices[0].message.content
