"""工具白名单注册、定义导出与安全分发。"""

import json
from copy import deepcopy

from app.schemas.tool import ToolCall, ToolDefinition, ToolExecutionResult
from app.tools.base import Tool


class ToolRegistry:
    """只允许模型调用显式注册的工具。

    Registry 是工具执行的安全边界：模型输出的工具名和参数都只是非可信数据，
    不能被当成 Python 函数、模块名称或系统命令直接执行。
    """

    def __init__(self, tools: list[Tool] | None = None) -> None:
        self._tools: dict[str, Tool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        """注册工具；重复名称会在启动阶段立即报错。"""
        if tool.name in self._tools:
            raise ValueError(f"工具名称重复: {tool.name}")
        self._tools[tool.name] = tool

    def get_definitions(self) -> list[ToolDefinition]:
        """返回工具定义副本，防止 Provider 或 SDK 修改注册信息。"""
        return [deepcopy(tool.definition) for tool in self._tools.values()]

    def execute(self, tool_call: ToolCall) -> ToolExecutionResult:
        """解析参数并执行白名单工具，将所有可恢复错误结构化。"""
        tool = self._tools.get(tool_call.name)
        if tool is None:
            return self._failure(tool_call, f"未注册的工具: {tool_call.name}")

        try:
            arguments = json.loads(tool_call.arguments)
        except json.JSONDecodeError:
            return self._failure(tool_call, "工具参数不是有效的 JSON 对象")

        if not isinstance(arguments, dict):
            return self._failure(tool_call, "工具参数必须是 JSON 对象")

        try:
            output = tool.execute(arguments)
        except ValueError as exc:
            # 参数校验错误可以安全返回模型，由模型向用户组织友好回答。
            return self._failure(tool_call, str(exc) or "工具执行失败")
        except Exception:
            # 未预期异常可能包含内部实现或敏感信息，不能原样暴露给模型。
            return self._failure(tool_call, "工具执行失败")

        return ToolExecutionResult(
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            success=True,
            output=output,
        )

    @staticmethod
    def _failure(tool_call: ToolCall, error: str) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            success=False,
            error=error,
        )
