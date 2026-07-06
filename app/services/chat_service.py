from app.providers.openai_provider import OpenAIProvider


class ChatService:
    """
    聊天业务层

    负责处理聊天相关业务，
    调用 Provider 获取 AI 回复。
    """

    def __init__(self):
        self.provider = OpenAIProvider()

    def chat(self, message: str) -> str:
        """
        聊天入口
        """

        reply = self.provider.chat(message)

        return reply