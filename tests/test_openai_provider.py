"""OpenAIProvider 对 SDK 响应的领域转换测试。"""

import unittest
from types import SimpleNamespace

from app.providers.openai_provider import InvalidModelResponseError, OpenAIProvider
from app.schemas.tool import ToolDefinition


class FakeCompletions:
    def __init__(self, response: object | list[object]) -> None:
        responses = response if isinstance(response, list) else [response]
        self._responses = iter(responses)
        self.request: dict | None = None
        self.call_count = 0

    def create(self, **kwargs: object) -> object:
        self.request = kwargs
        self.call_count += 1
        return next(self._responses)


class FakeClient:
    def __init__(self, response: object) -> None:
        self.completions = FakeCompletions(response)
        self.chat = SimpleNamespace(completions=self.completions)


class OpenAIProviderTestCase(unittest.TestCase):
    def test_missing_choices_is_reported_as_provider_error(self) -> None:
        empty = SimpleNamespace(choices=None)
        client = FakeClient([empty, empty])
        provider = OpenAIProvider(client=client, empty_response_retries=1)

        with self.assertRaisesRegex(InvalidModelResponseError, "没有可用的 choices"):
            provider.chat([{"role": "user", "content": "你好"}])

        self.assertEqual(client.completions.call_count, 2)

    def test_empty_response_is_retried_before_succeeding(self) -> None:
        empty = SimpleNamespace(choices=None)
        message = SimpleNamespace(content="重试成功", tool_calls=None)
        valid = SimpleNamespace(choices=[SimpleNamespace(message=message)])
        client = FakeClient([empty, valid])
        provider = OpenAIProvider(client=client, empty_response_retries=1)

        result = provider.chat([{"role": "user", "content": "你好"}])

        self.assertEqual(result.content, "重试成功")
        self.assertEqual(client.completions.call_count, 2)

    def test_text_response_is_converted(self) -> None:
        message = SimpleNamespace(content="普通回答", tool_calls=None)
        response = SimpleNamespace(choices=[SimpleNamespace(message=message)])
        client = FakeClient(response)
        provider = OpenAIProvider(client=client)

        result = provider.chat([{"role": "user", "content": "你好"}])

        self.assertEqual(result.content, "普通回答")
        self.assertFalse(result.requests_tools)
        self.assertNotIn("tools", client.completions.request)

    def test_tool_calls_and_definitions_are_converted(self) -> None:
        sdk_tool_call = SimpleNamespace(
            id="call-1",
            function=SimpleNamespace(
                name="get_current_time",
                arguments='{"timezone":"Asia/Tokyo"}',
            ),
        )
        message = SimpleNamespace(content=None, tool_calls=[sdk_tool_call])
        response = SimpleNamespace(choices=[SimpleNamespace(message=message)])
        client = FakeClient(response)
        provider = OpenAIProvider(client=client)
        tools: list[ToolDefinition] = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "获取时间",
                    "parameters": {"type": "object"},
                },
            }
        ]

        result = provider.chat(
            [{"role": "user", "content": "东京几点？"}],
            tools=tools,
        )

        self.assertTrue(result.requests_tools)
        self.assertEqual(result.tool_calls[0].id, "call-1")
        self.assertEqual(result.tool_calls[0].name, "get_current_time")
        self.assertEqual(client.completions.request["tools"], tools)


if __name__ == "__main__":
    unittest.main()
