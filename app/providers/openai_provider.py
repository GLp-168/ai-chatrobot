"""OpenAI 兼容大模型的访问适配器。"""

from collections.abc import Sequence

from openai import OpenAI

from app.core.setting import Settings
from app.schemas.message import ChatMessage
from app.schemas.model import ModelResponse
from app.schemas.tool import ToolCall, ToolDefinition


class InvalidModelResponseError(RuntimeError):
    """兼容 API 返回了缺少 choices 的非标准响应。"""


class OpenAIProvider:
    """把应用内部的聊天消息转换为一次 OpenAI 兼容 API 调用。"""

    def __init__(self, client: OpenAI | None = None) -> None:
        # client 参数用于单元测试注入假 SDK；正式运行时才创建真实客户端。
        self.client = client or OpenAI(
            api_key=Settings.OPENAI_API_KEY,
            base_url=Settings.OPENAI_BASE_URL,
        )

    def chat(
        self,
        messages: list[ChatMessage],
        tools: Sequence[ToolDefinition] | None = None,
    ) -> ModelResponse:
        """调用兼容 API，并把厂商响应转换成应用领域对象。"""
        request: dict[str, object] = {
            "model": Settings.MODEL_NAME,
            "messages": messages,
        }
        if tools:
            request["tools"] = list(tools)

        response = self.client.chat.completions.create(**request)
        if not response.choices:
            raise InvalidModelResponseError("模型响应中没有可用的 choices")

        message = response.choices[0].message

        tool_calls = tuple(
            ToolCall(
                id=tool_call.id,
                name=tool_call.function.name,
                arguments=tool_call.function.arguments,
            )
            for tool_call in (message.tool_calls or [])
        )

        return ModelResponse(
            content=message.content,
            tool_calls=tool_calls,
        )
