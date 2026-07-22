"""所有本地工具必须遵守的最小契约。"""

from typing import Any, Protocol

from app.schemas.tool import ToolDefinition


class Tool(Protocol):
    """可以注册到 ToolRegistry 的工具协议。"""

    name: str

    @property
    def definition(self) -> ToolDefinition:
        """返回提供给模型的名称、说明和参数 JSON Schema。"""
        ...

    def execute(self, arguments: dict[str, Any]) -> Any:
        """执行经过 JSON 解析后的参数并返回可序列化结果。"""
        ...
