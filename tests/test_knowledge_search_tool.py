"""KnowledgeSearchTool 参数边界与引用结果测试。"""

import unittest

from app.knowledge.models import KnowledgeChunk
from app.knowledge.retriever import BM25Retriever
from app.tools.knowledge_search import KnowledgeSearchTool


class KnowledgeSearchToolTestCase(unittest.TestCase):
    def setUp(self) -> None:
        retriever = BM25Retriever(
            [
                KnowledgeChunk(
                    id="chunk-memory",
                    source="project.md",
                    position=0,
                    content="Memory 只保存用户消息和最终回复。",
                ),
                KnowledgeChunk(
                    id="chunk-prompt",
                    source="project.md",
                    position=1,
                    content="PromptManager 负责组合系统提示词和聊天历史。",
                ),
            ]
        )
        self.tool = KnowledgeSearchTool(
            retriever=retriever,
            default_top_k=1,
            max_top_k=2,
            max_query_characters=20,
        )

    def test_results_include_real_source_and_chunk_id(self) -> None:
        output = self.tool.execute({"query": "Memory 保存什么"})

        self.assertEqual(len(output["matches"]), 1)
        self.assertEqual(output["matches"][0]["source"], "project.md")
        self.assertEqual(output["matches"][0]["chunk_id"], "chunk-memory")
        self.assertIn("引用", output["message"])

    def test_no_match_returns_explicit_empty_result(self) -> None:
        output = self.tool.execute({"query": "量子计算"})

        self.assertEqual(output["matches"], [])
        self.assertIn("没有找到", output["message"])

    def test_query_and_top_k_are_validated(self) -> None:
        with self.assertRaisesRegex(ValueError, "query"):
            self.tool.execute({"query": " "})

        with self.assertRaisesRegex(ValueError, "top_k 必须是整数"):
            self.tool.execute({"query": "Memory", "top_k": True})

        with self.assertRaisesRegex(ValueError, "1 到 2"):
            self.tool.execute({"query": "Memory", "top_k": 3})

        with self.assertRaisesRegex(ValueError, "不能超过 20"):
            self.tool.execute({"query": "超" * 21})

    def test_definition_exposes_model_parameter_limits(self) -> None:
        parameters = self.tool.definition["function"]["parameters"]

        self.assertEqual(parameters["properties"]["top_k"]["maximum"], 2)
        self.assertEqual(parameters["properties"]["query"]["maxLength"], 20)
        self.assertFalse(parameters["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
