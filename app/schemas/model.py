"""Provider 返回给业务层的统一模型响应。"""

from dataclasses import dataclass

from app.schemas.message import ChatMessage
from app.schemas.tool import ToolCall


@dataclass(frozen=True)
class ModelResponse:
    """同时支持最终文本和工具调用的模型响应。

    Service 只依赖这个领域对象，不接触 OpenAI SDK 的响应类。未来替换模型
    Provider 时，只需要在 Provider 内把厂商响应转换成同一结构。
    """

    content: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()

    @property
    def requests_tools(self) -> bool:
        """模型是否请求执行至少一个工具。"""
        return bool(self.tool_calls)

    def to_assistant_message(self) -> ChatMessage:
        """转换为继续工具闭环所需的 assistant 消息。"""
        message: ChatMessage = {
            "role": "assistant",
            "content": self.content,
        }
        if self.tool_calls:
            message["tool_calls"] = [
                tool_call.to_assistant_payload() for tool_call in self.tool_calls
            ]
        return message
