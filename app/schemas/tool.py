"""工具定义、调用和执行结果的领域对象。"""

import json
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from app.schemas.message import AssistantToolCall, ChatMessage


class FunctionDefinition(TypedDict):
    """提供给模型的函数说明与 JSON Schema 参数定义。"""

    name: str
    description: str
    parameters: dict[str, Any]


class ToolDefinition(TypedDict):
    """OpenAI 兼容的 function tool 定义。"""

    type: Literal["function"]
    function: FunctionDefinition


@dataclass(frozen=True)
class ToolCall:
    """Provider 从模型响应中解析出的工具调用意图。"""

    id: str
    name: str
    arguments: str

    def to_assistant_payload(self) -> AssistantToolCall:
        """转换为下一次模型调用需要携带的 assistant tool_call。"""
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": self.arguments,
            },
        }


@dataclass(frozen=True)
class ToolExecutionResult:
    """一次工具执行的成功结果或可恢复错误。"""

    tool_call_id: str
    tool_name: str
    success: bool
    output: Any = None
    error: str | None = None

    def to_message(self) -> ChatMessage:
        """序列化为 role=tool 的消息，让模型可以读取执行结果。"""
        payload = (
            {"ok": True, "result": self.output}
            if self.success
            else {"ok": False, "error": self.error}
        )
        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "content": json.dumps(payload, ensure_ascii=False, default=str),
        }
