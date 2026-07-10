"""运行期聊天记录的存储与读取。"""

from app.schemas.message import ChatMessage


class ChatMemory:
    """在当前 Python 进程中保存一段对话的上下文。

    这一版 Memory 有意保持简单：它只管理消息，不关心 HTTP、Prompt、
    大模型或数据库。服务重启后记录会丢失，这是运行期内存存储的预期行为。
    """

    def __init__(self) -> None:
        # 使用私有属性，避免调用方绕过 add_* 方法直接修改内部状态。
        self._messages: list[ChatMessage] = []

    def add_user_message(self, content: str) -> None:
        """按 OpenAI 兼容格式保存一条用户消息。"""
        self._messages.append(
            {
                "role": "user",
                "content": content,
            }
        )

    def add_assistant_message(self, content: str) -> None:
        """按 OpenAI 兼容格式保存一条 AI 回复。"""
        self._messages.append(
            {
                "role": "assistant",
                "content": content,
            }
        )

    def get_messages(self) -> list[ChatMessage]:
        """返回当前全部消息的副本，并保持消息的原始顺序。

        返回副本很重要：Provider 只应该读取上下文，不应该能够意外修改
        Memory 的内部列表或其中的消息字典。
        """
        return [message.copy() for message in self._messages]

    def clear(self) -> None:
        """清空当前进程中保存的全部聊天记录。"""
        self._messages.clear()
