"""PromptManager 的单元测试。"""

import unittest

from app.prompts.prompt_manager import PromptManager


class PromptManagerTestCase(unittest.TestCase):
    def test_system_prompt_is_added_before_history(self) -> None:
        manager = PromptManager(
            system_prompt="你是一名 Python 导师。",
            max_history_messages=10,
        )
        history = [
            {"role": "user", "content": "什么是列表？"},
            {"role": "assistant", "content": "列表是一种有序容器。"},
        ]

        messages = manager.build_messages(history)

        self.assertEqual(
            messages,
            [
                {"role": "system", "content": "你是一名 Python 导师。"},
                {"role": "user", "content": "什么是列表？"},
                {"role": "assistant", "content": "列表是一种有序容器。"},
            ],
        )
        self.assertEqual(history[0]["content"], "什么是列表？")

    def test_old_history_is_trimmed_without_orphan_assistant_message(self) -> None:
        manager = PromptManager(
            system_prompt="保持简洁。",
            max_history_messages=4,
        )
        history = [
            {"role": "user", "content": "问题一"},
            {"role": "assistant", "content": "回答一"},
            {"role": "user", "content": "问题二"},
            {"role": "assistant", "content": "回答二"},
            {"role": "user", "content": "问题三"},
        ]

        messages = manager.build_messages(history)

        self.assertEqual(
            messages,
            [
                {"role": "system", "content": "保持简洁。"},
                {"role": "user", "content": "问题二"},
                {"role": "assistant", "content": "回答二"},
                {"role": "user", "content": "问题三"},
            ],
        )

    def test_configured_system_prompt_replaces_history_system_messages(self) -> None:
        manager = PromptManager(
            system_prompt="当前系统指令",
            max_history_messages=10,
        )

        messages = manager.build_messages(
            [
                {"role": "system", "content": "过期系统指令"},
                {"role": "user", "content": "你好"},
            ]
        )

        self.assertEqual(
            messages,
            [
                {"role": "system", "content": "当前系统指令"},
                {"role": "user", "content": "你好"},
            ],
        )

    def test_invalid_configuration_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "system_prompt 不能为空"):
            PromptManager(system_prompt="   ", max_history_messages=10)

        with self.assertRaisesRegex(ValueError, "max_history_messages 必须大于 0"):
            PromptManager(system_prompt="有效指令", max_history_messages=0)


if __name__ == "__main__":
    unittest.main()
