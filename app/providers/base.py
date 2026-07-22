"""模型 Provider 需要遵守的应用层契约。"""

from collections.abc import Sequence
from typing import Protocol

from app.schemas.message import ChatMessage
from app.schemas.model import ModelResponse
from app.schemas.tool import ToolDefinition


class ChatProvider(Protocol):
    """任何聊天模型适配器都需要实现的最小接口。

    Protocol 使用结构化类型：实现类不需要继承它，只要提供相同签名的 chat
    方法即可。这让 OpenAI、GLM、Claude 或测试 FakeProvider 都能被 Service 使用。
    """

    def chat(
        self,
        messages: list[ChatMessage],
        tools: Sequence[ToolDefinition] | None = None,
    ) -> ModelResponse:
        """接收消息和可用工具，并返回统一模型响应。"""
        ...
