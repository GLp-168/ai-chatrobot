"""聊天业务流程与 Tool Calling 闭环的编排。"""

from app.core.setting import Settings
from app.memory.chat_memory import ChatMemory
from app.prompts.prompt_manager import PromptManager
from app.providers.base import ChatProvider
from app.providers.openai_provider import OpenAIProvider
from app.tools.defaults import create_default_tool_registry
from app.tools.registry import ToolRegistry


class ToolRoundLimitError(RuntimeError):
    """模型持续请求工具并超过单次请求允许的最大轮数。"""


class ChatService:
    """编排聊天、Prompt、模型调用和工具执行。

    Service 不实现具体工具，也不理解某家模型 SDK。它只维护请求生命周期：
    保存用户消息、构建 Prompt、调用模型、执行工具、再次调用模型、保存最终回复。
    """

    def __init__(
        self,
        provider: ChatProvider | None = None,
        memory: ChatMemory | None = None,
        prompt_manager: PromptManager | None = None,
        tool_registry: ToolRegistry | None = None,
        max_tool_rounds: int | None = None,
    ) -> None:
        self.provider = provider if provider is not None else OpenAIProvider()
        self.memory = memory if memory is not None else ChatMemory()
        self.prompt_manager = (
            prompt_manager
            if prompt_manager is not None
            else PromptManager(
                system_prompt=Settings.SYSTEM_PROMPT,
                max_history_messages=Settings.MAX_HISTORY_MESSAGES,
            )
        )
        self.tool_registry = (
            tool_registry
            if tool_registry is not None
            else create_default_tool_registry()
        )
        self.max_tool_rounds = (
            max_tool_rounds
            if max_tool_rounds is not None
            else Settings.MAX_TOOL_ROUNDS
        )
        if self.max_tool_rounds < 1:
            raise ValueError("max_tool_rounds 必须大于 0")

    def chat(self, message: str) -> str:
        """处理用户消息，必要时执行工具，最终返回模型文本。"""
        self.memory.add_user_message(message)

        history = self.memory.get_messages()
        prompt_messages = self.prompt_manager.build_messages(history)
        tool_definitions = self.tool_registry.get_definitions()
        completed_tool_rounds = 0

        while True:
            model_response = self.provider.chat(
                prompt_messages,
                tools=tool_definitions,
            )

            if not model_response.requests_tools:
                reply = model_response.content
                if reply is None or not reply.strip():
                    raise RuntimeError("模型既没有返回文本，也没有请求调用工具")

                # Memory 只保存用户可见的最终对话，不保存请求内部的工具轨迹。
                self.memory.add_assistant_message(reply)
                return reply

            if completed_tool_rounds >= self.max_tool_rounds:
                raise ToolRoundLimitError(
                    f"工具调用超过最大轮数: {self.max_tool_rounds}"
                )

            # OpenAI 协议要求先回放包含 tool_calls 的 assistant 消息，再逐项追加
            # 对应 tool_call_id 的工具结果，之后模型才能基于结果继续推理。
            prompt_messages.append(model_response.to_assistant_message())
            for tool_call in model_response.tool_calls:
                execution_result = self.tool_registry.execute(tool_call)
                prompt_messages.append(execution_result.to_message())

            completed_tool_rounds += 1
