"""ChatService 多轮对话流程的单元测试。"""

import unittest

from app.memory.chat_memory import ChatMemory
from app.prompts.prompt_manager import PromptManager
from app.schemas.message import ChatMessage
from app.services.chat_service import ChatService


class FakeProvider:
    """记录收到的上下文，避免单元测试真实调用 GLM。"""

    def __init__(self, replies: list[str]) -> None:
        self._replies = iter(replies)
        self.received_messages: list[list[ChatMessage]] = []

    def chat(self, messages: list[ChatMessage]) -> str:
        self.received_messages.append(messages)
        return next(self._replies)


class ChatServiceTestCase(unittest.TestCase):
    def test_second_request_contains_previous_conversation(self) -> None:
        provider = FakeProvider(["你好，小李", "你叫小李"])
        memory = ChatMemory()
        prompt_manager = PromptManager(
            system_prompt="你是一个测试助手。",
            max_history_messages=10,
        )
        service = ChatService(
            provider=provider,
            memory=memory,
            prompt_manager=prompt_manager,
        )

        first_reply = service.chat("我叫小李")
        second_reply = service.chat("我叫什么？")

        self.assertEqual(first_reply, "你好，小李")
        self.assertEqual(second_reply, "你叫小李")
        self.assertEqual(
            provider.received_messages,
            [
                [
                    {"role": "system", "content": "你是一个测试助手。"},
                    {"role": "user", "content": "我叫小李"},
                ],
                [
                    {"role": "system", "content": "你是一个测试助手。"},
                    {"role": "user", "content": "我叫小李"},
                    {"role": "assistant", "content": "你好，小李"},
                    {"role": "user", "content": "我叫什么？"},
                ],
            ],
        )
        self.assertEqual(
            memory.get_messages(),
            [
                {"role": "user", "content": "我叫小李"},
                {"role": "assistant", "content": "你好，小李"},
                {"role": "user", "content": "我叫什么？"},
                {"role": "assistant", "content": "你叫小李"},
            ],
        )
        self.assertNotIn(
            {"role": "system", "content": "你是一个测试助手。"},
            memory.get_messages(),
        )


if __name__ == "__main__":
    unittest.main()
