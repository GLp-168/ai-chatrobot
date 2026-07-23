"""TextChunker 段落合并、长文本切分与稳定 ID 测试。"""

import unittest

from app.knowledge.chunker import TextChunker
from app.knowledge.models import Document


class TextChunkerTestCase(unittest.TestCase):
    def test_short_paragraphs_are_combined_within_limit(self) -> None:
        document = Document(
            source="guide.md",
            content="第一段\n\n第二段\n\n这是明显更长的第三段",
        )
        chunker = TextChunker(max_characters=12, overlap=2)

        chunks = chunker.split_documents([document])

        self.assertEqual([chunk.content for chunk in chunks], ["第一段\n\n第二段", "这是明显更长的第三段"])
        self.assertEqual([chunk.position for chunk in chunks], [0, 1])
        self.assertTrue(all(len(chunk.content) <= 12 for chunk in chunks))

    def test_long_paragraph_uses_overlapping_windows(self) -> None:
        document = Document(source="long.txt", content="0123456789ABCDEFGH")
        chunker = TextChunker(max_characters=10, overlap=2)

        chunks = chunker.split_documents([document])

        self.assertEqual(
            [chunk.content for chunk in chunks],
            ["0123456789", "89ABCDEFGH"],
        )

    def test_chunk_ids_are_stable_for_same_input(self) -> None:
        document = Document(source="stable.md", content="稳定内容")
        chunker = TextChunker(max_characters=20, overlap=2)

        first = chunker.split_documents([document])
        second = chunker.split_documents([document])

        self.assertEqual(first[0].id, second[0].id)
        self.assertTrue(first[0].id.startswith("chunk-"))

    def test_invalid_chunk_configuration_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "max_characters"):
            TextChunker(max_characters=0)

        with self.assertRaisesRegex(ValueError, "overlap"):
            TextChunker(max_characters=10, overlap=10)


if __name__ == "__main__":
    unittest.main()
