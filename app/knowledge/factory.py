"""组装本地知识检索流水线。"""

from pathlib import Path

from app.knowledge.chunker import TextChunker
from app.knowledge.loader import DocumentLoader
from app.knowledge.retriever import BM25Retriever


def create_knowledge_retriever(
    knowledge_dir: Path,
    chunk_size: int,
    chunk_overlap: int,
) -> BM25Retriever:
    """加载文档、完成切片并构建一个可复用的内存 BM25 索引。"""
    documents = DocumentLoader(knowledge_dir).load()
    chunks = TextChunker(
        max_characters=chunk_size,
        overlap=chunk_overlap,
    ).split_documents(documents)
    return BM25Retriever(chunks)
