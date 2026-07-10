"""ChatMemory 的单元测试。"""

import unittest

from app.memory.chat_memory import ChatMemory


class ChatMemoryTestCase(unittest.TestCase):
    def test_messages_are_saved_in_conversation_order(self) -> None:
        memory = ChatMemory()

        memory.add_user_message("我叫小李")
        memory.add_assistant_message("你好，小李")

        self.assertEqual(
            memory.get_messages(),
            [
                {"role": "user", "content": "我叫小李"},
                {"role": "assistant", "content": "你好，小李"},
            ],
        )

    def test_returned_messages_cannot_modify_memory(self) -> None:
        memory = ChatMemory()
        memory.add_user_message("你好")

        messages = memory.get_messages()
        messages[0]["content"] = "被外部修改"
        messages.append({"role": "assistant", "content": "额外消息"})

        self.assertEqual(
            memory.get_messages(),
            [{"role": "user", "content": "你好"}],
        )

    def test_clear_removes_all_messages(self) -> None:
        memory = ChatMemory()
        memory.add_user_message("你好")
        memory.add_assistant_message("你好")

        memory.clear()

        self.assertEqual(memory.get_messages(), [])


if __name__ == "__main__":
    unittest.main()
