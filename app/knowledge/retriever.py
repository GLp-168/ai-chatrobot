"""基于中文分词和 BM25 的内存知识检索器。"""

import logging

import jieba
from rank_bm25 import BM25Plus

from app.knowledge.models import KnowledgeChunk, SearchResult


class BM25Retriever:
    """对知识切片建立一次内存索引，并返回最相关的 Top-K。"""

    def __init__(self, chunks: list[KnowledgeChunk]) -> None:
        jieba.setLogLevel(logging.WARNING)
        self._tokenizer = jieba.Tokenizer()
        searchable_chunks = [
            (chunk, self._tokenize(chunk.content)) for chunk in chunks
        ]
        searchable_chunks = [item for item in searchable_chunks if item[1]]

        self._chunks = [chunk for chunk, _ in searchable_chunks]
        self._tokenized_chunks = [tokens for _, tokens in searchable_chunks]
        self._token_sets = [set(tokens) for tokens in self._tokenized_chunks]
        self._index = (
            BM25Plus(self._tokenized_chunks) if self._tokenized_chunks else None
        )

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        """检索至少与查询共享一个有效词元的相关切片。"""
        if top_k < 1:
            raise ValueError("top_k 必须大于 0")

        query_tokens = self._tokenize(query)
        if not query_tokens or self._index is None:
            return []

        query_token_set = set(query_tokens)
        scores = self._index.get_scores(query_tokens)
        candidates = [
            (index, float(scores[index]))
            for index, token_set in enumerate(self._token_sets)
            if query_token_set & token_set
        ]
        candidates.sort(key=lambda item: (-item[1], item[0]))

        return [
            SearchResult(chunk=self._chunks[index], score=score)
            for index, score in candidates[:top_k]
        ]

    def _tokenize(self, text: str) -> list[str]:
        """保留包含字母或数字的中英文搜索词，忽略空白和标点。"""
        return [
            token.lower().strip()
            for token in self._tokenizer.lcut_for_search(text)
            if token.strip() and any(character.isalnum() for character in token)
        ]
