"""聊天业务流程的编排。"""

from app.memory.chat_memory import ChatMemory
from app.providers.openai_provider import OpenAIProvider


class ChatService:
    """编排一次完整聊天请求的业务步骤。

    Service 不负责保存数据的具体方式，也不负责调用某家模型的 SDK。
    它只规定顺序：保存用户消息、读取上下文、调用 Provider、保存 AI 回复。
    """

    def __init__(
        self,
        provider: OpenAIProvider | None = None,
        memory: ChatMemory | None = None,
    ) -> None:
        # 默认依赖用于正式运行；构造参数允许测试时注入假 Provider 和 Memory。
        self.provider = provider if provider is not None else OpenAIProvider()
        self.memory = memory if memory is not None else ChatMemory()

    def chat(self, message: str) -> str:
        """处理一条用户消息并返回包含历史上下文的模型回复。"""
        # 先保存本轮输入，确保发送给模型的上下文包含用户刚说的话。
        self.memory.add_user_message(message)

        # Memory 负责消息格式和顺序，Provider 只负责把完整消息列表发给模型。
        messages = self.memory.get_messages()
        reply = self.provider.chat(messages)

        # 只有获得模型回复后才记录 assistant 消息，形成完整的一问一答。
        self.memory.add_assistant_message(reply)

        return reply
