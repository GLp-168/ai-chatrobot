"""面向普通 Markdown/文本的段落切片策略。"""

import hashlib
import re

from app.knowledge.models import Document, KnowledgeChunk


class TextChunker:
    """优先保持段落完整，并限制每个切片的最大字符数。

    短段落会被合并以减少碎片；超过上限的单个长段落使用固定窗口和少量重叠
    切分，避免相关语句恰好落在边界两侧。
    """

    def __init__(self, max_characters: int = 800, overlap: int = 80) -> None:
        if max_characters < 1:
            raise ValueError("max_characters 必须大于 0")
        if overlap < 0 or overlap >= max_characters:
            raise ValueError("overlap 必须大于等于 0 且小于 max_characters")

        self._max_characters = max_characters
        self._overlap = overlap

    def split_documents(self, documents: list[Document]) -> list[KnowledgeChunk]:
        """将多份文档转换为带稳定来源与顺序的知识切片。"""
        chunks: list[KnowledgeChunk] = []
        for document in documents:
            texts = self._split_text(document.content)
            for position, content in enumerate(texts):
                chunks.append(
                    KnowledgeChunk(
                        id=self._build_id(document.source, position, content),
                        source=document.source,
                        position=position,
                        content=content,
                    )
                )
        return chunks

    def _split_text(self, text: str) -> list[str]:
        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(r"\n\s*\n", text)
            if paragraph.strip()
        ]
        chunks: list[str] = []
        pending: list[str] = []
        pending_length = 0

        def flush_pending() -> None:
            nonlocal pending, pending_length
            if pending:
                chunks.append("\n\n".join(pending))
                pending = []
                pending_length = 0

        for paragraph in paragraphs:
            if len(paragraph) > self._max_characters:
                flush_pending()
                chunks.extend(self._split_long_paragraph(paragraph))
                continue

            separator_length = 2 if pending else 0
            if pending_length + separator_length + len(paragraph) > self._max_characters:
                flush_pending()

            pending.append(paragraph)
            pending_length += (2 if len(pending) > 1 else 0) + len(paragraph)

        flush_pending()
        return chunks

    def _split_long_paragraph(self, paragraph: str) -> list[str]:
        step = self._max_characters - self._overlap
        chunks: list[str] = []
        start = 0
        while start < len(paragraph):
            end = start + self._max_characters
            chunks.append(paragraph[start:end])
            if end >= len(paragraph):
                break
            start += step
        return chunks

    @staticmethod
    def _build_id(source: str, position: int, content: str) -> str:
        identity = f"{source}\0{position}\0{content}".encode("utf-8")
        digest = hashlib.sha256(identity).hexdigest()[:12]
        return f"chunk-{digest}"
