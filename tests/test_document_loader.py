"""DocumentLoader 文件范围与格式测试。"""

import tempfile
import unittest
from pathlib import Path

from app.knowledge.loader import DocumentLoader


class DocumentLoaderTestCase(unittest.TestCase):
    def test_supported_non_empty_documents_are_loaded_in_source_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "nested"
            nested.mkdir()
            (root / "b.txt").write_text("文本资料", encoding="utf-8")
            (nested / "a.md").write_text("\ufeff# Markdown 资料", encoding="utf-8")
            (root / "ignored.json").write_text("{}", encoding="utf-8")
            (root / "empty.md").write_text("   ", encoding="utf-8")

            documents = DocumentLoader(root).load()

        self.assertEqual(
            [(document.source, document.content) for document in documents],
            [
                ("b.txt", "文本资料"),
                ("nested/a.md", "# Markdown 资料"),
            ],
        )

    def test_missing_knowledge_directory_is_rejected(self) -> None:
        missing = Path("directory-that-does-not-exist")

        with self.assertRaisesRegex(FileNotFoundError, "知识库目录不存在"):
            DocumentLoader(missing).load()


if __name__ == "__main__":
    unittest.main()
