"""聊天流程各层共享的 OpenAI 兼容消息结构。"""

from typing import Literal, Required, TypedDict


class FunctionCallPayload(TypedDict):
    """模型在一次工具调用中生成的函数名称与 JSON 参数。"""

    name: str
    arguments: str


class AssistantToolCall(TypedDict):
    """assistant 消息中携带的一项工具调用请求。"""

    id: str
    type: Literal["function"]
    function: FunctionCallPayload


class ChatMessage(TypedDict, total=False):
    """一条可发送给 OpenAI 兼容模型的消息。

    不同 role 需要不同字段，因此使用 ``total=False`` 表达可选字段：
    普通消息使用 content，assistant 工具请求使用 tool_calls，工具执行结果使用
    tool_call_id。role 本身通过 Required 保持必填。
    """

    role: Required[Literal["user", "assistant", "system", "tool"]]
    content: str | None
    tool_calls: list[AssistantToolCall]
    tool_call_id: str
