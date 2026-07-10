"""聊天业务流程的编排。"""

from app.core.setting import Settings
from app.memory.chat_memory import ChatMemory
from app.prompts.prompt_manager import PromptManager
from app.providers.base import ChatProvider
from app.providers.openai_provider import OpenAIProvider


class ChatService:
    """编排一次完整聊天请求的业务步骤。

    Service 不负责保存数据的具体方式，也不负责调用某家模型的 SDK。
    它只规定顺序：保存用户消息、读取上下文、构建 Prompt、调用 Provider、
    保存 AI 回复。
    """

    def __init__(
        self,
        provider: ChatProvider | None = None,
        memory: ChatMemory | None = None,
        prompt_manager: PromptManager | None = None,
    ) -> None:
        # 默认依赖用于正式运行；构造参数允许测试时替换外部依赖和构建策略。
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

    def chat(self, message: str) -> str:
        """处理一条用户消息并返回包含历史上下文的模型回复。"""
        # 先保存本轮输入，确保发送给模型的上下文包含用户刚说的话。
        self.memory.add_user_message(message)

        # Memory 提供事实历史，PromptManager 负责加入系统指令并控制上下文长度。
        history = self.memory.get_messages()
        prompt_messages = self.prompt_manager.build_messages(history)

        # Provider 收到的已经是最终 Prompt，不需要理解 Memory 或业务规则。
        reply = self.provider.chat(prompt_messages)

        # 只有获得模型回复后才记录 assistant 消息，形成完整的一问一答。
        self.memory.add_assistant_message(reply)

        return reply
