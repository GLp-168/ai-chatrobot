"""ToolRegistry 白名单和错误隔离测试。"""

import json
import unittest
from typing import Any

from app.schemas.tool import ToolCall, ToolDefinition
from app.tools.registry import ToolRegistry


class SampleTool:
    name = "sample"

    @property
    def definition(self) -> ToolDefinition:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "测试工具",
                "parameters": {"type": "object"},
            },
        }

    def execute(self, arguments: dict[str, Any]) -> Any:
        if arguments.get("fail"):
            raise ValueError("预期的工具错误")
        if arguments.get("internal_error"):
            raise RuntimeError("不应泄露的内部信息")
        return arguments


class ToolRegistryTestCase(unittest.TestCase):
    def test_registered_tool_is_executed(self) -> None:
        registry = ToolRegistry([SampleTool()])

        result = registry.execute(
            ToolCall(id="call-1", name="sample", arguments='{"value": 42}')
        )

        self.assertTrue(result.success)
        self.assertEqual(result.output, {"value": 42})
        self.assertEqual(
            json.loads(result.to_message()["content"]),
            {"ok": True, "result": {"value": 42}},
        )

    def test_unknown_tool_and_invalid_arguments_become_error_results(self) -> None:
        registry = ToolRegistry([SampleTool()])

        unknown = registry.execute(
            ToolCall(id="call-1", name="not_registered", arguments="{}")
        )
        invalid_json = registry.execute(
            ToolCall(id="call-2", name="sample", arguments="not-json")
        )
        non_object = registry.execute(
            ToolCall(id="call-3", name="sample", arguments="[]")
        )

        self.assertFalse(unknown.success)
        self.assertIn("未注册", unknown.error)
        self.assertFalse(invalid_json.success)
        self.assertIn("有效的 JSON", invalid_json.error)
        self.assertFalse(non_object.success)
        self.assertIn("JSON 对象", non_object.error)

    def test_tool_exception_becomes_error_result(self) -> None:
        registry = ToolRegistry([SampleTool()])

        result = registry.execute(
            ToolCall(id="call-1", name="sample", arguments='{"fail": true}')
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error, "预期的工具错误")

        internal_error = registry.execute(
            ToolCall(
                id="call-2",
                name="sample",
                arguments='{"internal_error": true}',
            )
        )
        self.assertFalse(internal_error.success)
        self.assertEqual(internal_error.error, "工具执行失败")

    def test_duplicate_tool_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "工具名称重复"):
            ToolRegistry([SampleTool(), SampleTool()])

    def test_returned_definitions_do_not_mutate_registry(self) -> None:
        registry = ToolRegistry([SampleTool()])

        definitions = registry.get_definitions()
        definitions[0]["function"]["description"] = "被外部修改"

        self.assertEqual(
            registry.get_definitions()[0]["function"]["description"],
            "测试工具",
        )


if __name__ == "__main__":
    unittest.main()
