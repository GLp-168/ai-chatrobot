"""知识库流水线中的领域对象。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    """从知识目录加载的一份原始文本及其相对来源路径。"""

    source: str
    content: str


@dataclass(frozen=True)
class KnowledgeChunk:
    """可以被独立检索和引用的一段文档内容。"""

    id: str
    source: str
    position: int
    content: str


@dataclass(frozen=True)
class SearchResult:
    """Retriever 返回的相关切片及其 BM25 分数。"""

    chunk: KnowledgeChunk
    score: float
