"""正式默认工具集合的组装测试。"""

import unittest

from app.tools.defaults import create_default_tool_registry


class DefaultToolsTestCase(unittest.TestCase):
    def test_time_and_knowledge_tools_are_registered(self) -> None:
        registry = create_default_tool_registry()

        names = [
            definition["function"]["name"]
            for definition in registry.get_definitions()
        ]

        self.assertEqual(names, ["get_current_time", "search_knowledge_base"])


if __name__ == "__main__":
    unittest.main()
