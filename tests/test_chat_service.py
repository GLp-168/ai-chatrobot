"""ChatService 多轮对话与 Tool Calling 闭环测试。"""

import json
import unittest
from collections.abc import Sequence
from copy import deepcopy
from typing import Any

from app.knowledge.models import KnowledgeChunk
from app.knowledge.retriever import BM25Retriever
from app.memory.chat_memory import ChatMemory
from app.prompts.prompt_manager import PromptManager
from app.schemas.message import ChatMessage
from app.schemas.model import ModelResponse
from app.schemas.tool import ToolCall, ToolDefinition
from app.services.chat_service import ChatService, ToolRoundLimitError
from app.tools.registry import ToolRegistry
from app.tools.knowledge_search import KnowledgeSearchTool


class FakeProvider:
    """按顺序返回预设响应，同时记录 Service 发来的完整请求。"""

    def __init__(self, responses: list[ModelResponse]) -> None:
        self._responses = iter(responses)
        self.received_messages: list[list[ChatMessage]] = []
        self.received_tools: list[list[ToolDefinition]] = []

    def chat(
        self,
        messages: list[ChatMessage],
        tools: Sequence[ToolDefinition] | None = None,
    ) -> ModelResponse:
        self.received_messages.append(deepcopy(messages))
        self.received_tools.append(deepcopy(list(tools or [])))
        return next(self._responses)


class EchoTool:
    """测试专用工具，直接返回模型提供的文本。"""

    name = "echo"

    @property
    def definition(self) -> ToolDefinition:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "返回输入文本",
                "parameters": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            },
        }

    def execute(self, arguments: dict[str, Any]) -> dict[str, str]:
        return {"text": str(arguments["text"])}


class ChatServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.prompt_manager = PromptManager(
            system_prompt="你是一个测试助手。",
            max_history_messages=10,
        )

    def test_second_request_contains_previous_conversation(self) -> None:
        provider = FakeProvider(
            [
                ModelResponse(content="你好，小李"),
                ModelResponse(content="你叫小李"),
            ]
        )
        memory = ChatMemory()
        service = ChatService(
            provider=provider,
            memory=memory,
            prompt_manager=self.prompt_manager,
            tool_registry=ToolRegistry(),
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

    def test_tool_result_is_sent_back_to_model_before_final_reply(self) -> None:
        provider = FakeProvider(
            [
                ModelResponse(
                    tool_calls=(
                        ToolCall(
                            id="call-1",
                            name="echo",
                            arguments='{"text": "工具结果"}',
                        ),
                    )
                ),
                ModelResponse(content="工具返回了：工具结果"),
            ]
        )
        memory = ChatMemory()
        service = ChatService(
            provider=provider,
            memory=memory,
            prompt_manager=self.prompt_manager,
            tool_registry=ToolRegistry([EchoTool()]),
        )

        reply = service.chat("请调用工具")

        self.assertEqual(reply, "工具返回了：工具结果")
        self.assertEqual(len(provider.received_messages), 2)
        second_request = provider.received_messages[1]
        self.assertEqual(second_request[-2]["role"], "assistant")
        self.assertEqual(second_request[-2]["tool_calls"][0]["id"], "call-1")
        self.assertEqual(second_request[-1]["role"], "tool")
        self.assertEqual(second_request[-1]["tool_call_id"], "call-1")
        self.assertEqual(
            json.loads(second_request[-1]["content"]),
            {"ok": True, "result": {"text": "工具结果"}},
        )
        self.assertEqual(
            provider.received_tools[0][0]["function"]["name"],
            "echo",
        )
        self.assertEqual(
            memory.get_messages(),
            [
                {"role": "user", "content": "请调用工具"},
                {"role": "assistant", "content": "工具返回了：工具结果"},
            ],
        )

    def test_repeated_tool_requests_are_stopped_by_round_limit(self) -> None:
        repeated_call = ModelResponse(
            tool_calls=(
                ToolCall(id="call-1", name="echo", arguments='{"text": "x"}'),
            )
        )
        provider = FakeProvider([repeated_call, repeated_call])
        memory = ChatMemory()
        service = ChatService(
            provider=provider,
            memory=memory,
            prompt_manager=self.prompt_manager,
            tool_registry=ToolRegistry([EchoTool()]),
            max_tool_rounds=1,
        )

        with self.assertRaisesRegex(ToolRoundLimitError, "最大轮数: 1"):
            service.chat("不断调用工具")

        self.assertEqual(len(provider.received_messages), 2)
        self.assertEqual(
            memory.get_messages(),
            [{"role": "user", "content": "不断调用工具"}],
        )

    def test_knowledge_tool_results_flow_back_with_citation_metadata(self) -> None:
        knowledge_tool = KnowledgeSearchTool(
            retriever=BM25Retriever(
                [
                    KnowledgeChunk(
                        id="chunk-memory",
                        source="architecture.md",
                        position=0,
                        content="工具轨迹不写入 Memory，而是进入独立审计日志。",
                    )
                ]
            )
        )
        provider = FakeProvider(
            [
                ModelResponse(
                    tool_calls=(
                        ToolCall(
                            id="call-rag",
                            name="search_knowledge_base",
                            arguments='{"query": "工具轨迹 Memory"}',
                        ),
                    )
                ),
                ModelResponse(
                    content="工具轨迹不写入 Memory。[architecture.md#chunk-memory]"
                ),
            ]
        )
        memory = ChatMemory()
        service = ChatService(
            provider=provider,
            memory=memory,
            prompt_manager=self.prompt_manager,
            tool_registry=ToolRegistry([knowledge_tool]),
        )

        reply = service.chat("为什么工具轨迹不写入 Memory？")

        tool_payload = json.loads(
            provider.received_messages[1][-1]["content"]
        )["result"]
        self.assertEqual(
            tool_payload["matches"][0]["source"],
            "architecture.md",
        )
        self.assertEqual(
            tool_payload["matches"][0]["chunk_id"],
            "chunk-memory",
        )
        self.assertIn("architecture.md#chunk-memory", reply)
        self.assertEqual(memory.get_messages()[-1]["content"], reply)

    def test_empty_model_response_is_rejected(self) -> None:
        service = ChatService(
            provider=FakeProvider([ModelResponse()]),
            memory=ChatMemory(),
            prompt_manager=self.prompt_manager,
            tool_registry=ToolRegistry(),
        )

        with self.assertRaisesRegex(RuntimeError, "既没有返回文本"):
            service.chat("你好")


if __name__ == "__main__":
    unittest.main()
