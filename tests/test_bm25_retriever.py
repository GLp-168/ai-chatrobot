"""BM25Retriever 中文检索与排序测试。"""

import unittest

from app.knowledge.models import KnowledgeChunk
from app.knowledge.retriever import BM25Retriever


class BM25RetrieverTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.chunks = [
            KnowledgeChunk(
                id="memory",
                source="architecture.md",
                position=0,
                content="工具调用轨迹不写入 Memory，应该进入独立审计日志。",
            ),
            KnowledgeChunk(
                id="deploy",
                source="deployment.md",
                position=0,
                content="生产环境使用 Docker 容器部署 FastAPI 服务。",
            ),
            KnowledgeChunk(
                id="weather",
                source="tools.md",
                position=0,
                content="天气工具通过外部接口查询温度和降水概率。",
            ),
        ]
        self.retriever = BM25Retriever(self.chunks)

    def test_relevant_chinese_chunk_is_ranked_first(self) -> None:
        results = self.retriever.search("为什么工具轨迹不放进 Memory", top_k=2)

        self.assertTrue(results)
        self.assertEqual(results[0].chunk.id, "memory")
        self.assertGreater(results[0].score, 0)

    def test_query_without_shared_tokens_returns_no_results(self) -> None:
        results = self.retriever.search("量子纠缠实验", top_k=3)

        self.assertEqual(results, [])

    def test_empty_index_and_invalid_top_k_are_handled(self) -> None:
        self.assertEqual(BM25Retriever([]).search("任何问题"), [])

        punctuation_only = KnowledgeChunk(
            id="punctuation",
            source="empty.md",
            position=0,
            content="--- !!!",
        )
        self.assertEqual(BM25Retriever([punctuation_only]).search("问题"), [])

        with self.assertRaisesRegex(ValueError, "top_k"):
            self.retriever.search("工具", top_k=0)


if __name__ == "__main__":
    unittest.main()
